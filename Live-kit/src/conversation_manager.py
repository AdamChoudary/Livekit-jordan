import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import redis
from redis.exceptions import ConnectionError, TimeoutError

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Manages conversation history using Redis for persistent storage.
    Provides session-based conversation tracking with automatic cleanup.
    """
    
    def __init__(self, redis_url: str = None, session_timeout: int = 3600, max_history: int = 50):
        """
        Initialize the conversation manager.
        
        Args:
            redis_url: Redis connection URL
            session_timeout: Session timeout in seconds (default: 1 hour)
            max_history: Maximum conversation turns to store per session
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL")
        self.session_timeout = session_timeout
        self.max_history = max_history
        self.redis_client = None
        
        # Initialize Redis connection
        self._connect_redis()
    
    def _connect_redis(self):
        """Establish Redis connection with error handling."""
        try:
            if not self.redis_url:
                logger.warning("No Redis URL provided. Conversation history will not be persistent.")
                return
            
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info("✅ Connected to Redis for conversation history")
            
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self.redis_client = None
        except Exception as e:
            logger.error(f"❌ Unexpected Redis error: {e}")
            self.redis_client = None
    
    def generate_session_id(self, participant_identity: str = None) -> str:
        """
        Generate a unique session ID for a participant.
        
        Args:
            participant_identity: Optional participant identifier
            
        Returns:
            Unique session ID
        """
        if participant_identity:
            # Use participant identity as base for consistent sessions
            base_id = f"session_{participant_identity}_{datetime.now().strftime('%Y%m%d')}"
        else:
            # Generate random session ID
            base_id = f"session_{uuid.uuid4().hex[:8]}"
        
        return base_id
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Dict = None) -> bool:
        """
        Add a message to the conversation history.
        
        Args:
            session_id: Session identifier
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            metadata: Optional metadata (order_id, product_id, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            logger.debug("Redis not available, skipping message storage")
            return False
        
        try:
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            # Store in Redis list
            key = f"conversation:{session_id}"
            
            # Add message to list
            self.redis_client.lpush(key, json.dumps(message))
            
            # Trim list to max_history
            self.redis_client.ltrim(key, 0, self.max_history - 1)
            
            # Set expiration
            self.redis_client.expire(key, self.session_timeout)
            
            logger.debug(f"Added {role} message to session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add message to Redis: {e}")
            return False
    
    def get_conversation_history(self, session_id: str, limit: int = None) -> List[Dict]:
        """
        Retrieve conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of conversation messages (newest first)
        """
        if not self.redis_client:
            return []
        
        try:
            key = f"conversation:{session_id}"
            limit = limit or self.max_history
            
            # Get messages from Redis (newest first)
            messages_json = self.redis_client.lrange(key, 0, limit - 1)
            
            messages = []
            for msg_json in messages_json:
                try:
                    message = json.loads(msg_json)
                    messages.append(message)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse message: {msg_json}")
                    continue
            
            # Reverse to get chronological order (oldest first)
            messages.reverse()
            
            logger.debug(f"Retrieved {len(messages)} messages for session {session_id}")
            return messages
            
        except Exception as e:
            logger.error(f"Failed to retrieve conversation history: {e}")
            return []
    
    def get_conversation_context(self, session_id: str, max_tokens: int = 2000) -> str:
        """
        Get conversation context as a formatted string for LLM.
        
        Args:
            session_id: Session identifier
            max_tokens: Approximate maximum tokens to include
            
        Returns:
            Formatted conversation context
        """
        messages = self.get_conversation_history(session_id)
        
        if not messages:
            return ""
        
        context_parts = []
        total_length = 0
        
        # Build context from most recent messages
        for message in reversed(messages):  # Start with newest
            role = message.get('role', 'unknown')
            content = message.get('content', '')
            timestamp = message.get('timestamp', '')
            
            # Format message
            if role == 'user':
                formatted = f"Customer: {content}"
            elif role == 'assistant':
                formatted = f"Agent: {content}"
            else:
                formatted = f"{role.title()}: {content}"
            
            # Check if adding this message would exceed token limit
            if total_length + len(formatted) > max_tokens:
                break
            
            context_parts.insert(0, formatted)  # Insert at beginning for chronological order
            total_length += len(formatted)
        
        if context_parts:
            return "Previous conversation:\n" + "\n".join(context_parts) + "\n\nCurrent query:"
        
        return ""
    
    def clear_session(self, session_id: str) -> bool:
        """
        Clear conversation history for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            key = f"conversation:{session_id}"
            self.redis_client.delete(key)
            logger.info(f"Cleared conversation history for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")
            return False
    
    def get_session_info(self, session_id: str) -> Dict:
        """
        Get session information and statistics.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with session info
        """
        if not self.redis_client:
            return {"status": "redis_unavailable"}
        
        try:
            key = f"conversation:{session_id}"
            
            # Get message count
            message_count = self.redis_client.llen(key)
            
            # Get TTL
            ttl = self.redis_client.ttl(key)
            
            # Get first and last message timestamps
            first_msg = None
            last_msg = None
            
            if message_count > 0:
                # Get oldest message (last in list)
                oldest_json = self.redis_client.lindex(key, -1)
                if oldest_json:
                    first_msg = json.loads(oldest_json).get('timestamp')
                
                # Get newest message (first in list)
                newest_json = self.redis_client.lindex(key, 0)
                if newest_json:
                    last_msg = json.loads(newest_json).get('timestamp')
            
            return {
                "status": "active" if message_count > 0 else "empty",
                "message_count": message_count,
                "ttl_seconds": ttl,
                "first_message": first_msg,
                "last_message": last_msg,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Failed to get session info: {e}")
            return {"status": "error", "error": str(e)}
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions (Redis handles this automatically, but this can be used for manual cleanup).
        
        Returns:
            Number of sessions cleaned up
        """
        if not self.redis_client:
            return 0
        
        try:
            # Get all conversation keys
            keys = self.redis_client.keys("conversation:*")
            cleaned = 0
            
            for key in keys:
                ttl = self.redis_client.ttl(key)
                if ttl == -2:  # Key doesn't exist
                    cleaned += 1
                elif ttl == -1:  # Key exists but has no expiration
                    # Set expiration for keys without TTL
                    self.redis_client.expire(key, self.session_timeout)
            
            logger.info(f"Cleaned up {cleaned} expired sessions")
            return cleaned
            
        except Exception as e:
            logger.error(f"Failed to cleanup sessions: {e}")
            return 0
    
    def is_connected(self) -> bool:
        """
        Check if Redis connection is active.
        
        Returns:
            True if connected, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except:
            return False
