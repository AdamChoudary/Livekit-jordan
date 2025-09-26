from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import uuid
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the text chat agent
from text_chat_agent import TextChatAgent

app = FastAPI(title="Text Chat Agent API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
agent = None

class ChatInitRequest(BaseModel):
    pass

class ChatMessageRequest(BaseModel):
    message: str
    sessionId: str

@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup."""
    global agent
    try:
        agent = TextChatAgent()
        logger.info("✅ Text Chat Agent initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Text Chat Agent: {e}")
        raise

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Text Chat Agent API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent_initialized": agent is not None,
        "gemini_available": agent.model is not None if agent else False
    }

@app.post("/api/chat/init")
async def init_chat():
    """Initialize a new chat session."""
    try:
        if not agent:
            raise HTTPException(status_code=500, detail="Agent not initialized")
        
        session_id = str(uuid.uuid4())
        greeting = await agent.start_chat_session(session_id)
        
        logger.info(f"✅ Chat session initialized: {session_id}")
        return {
            "sessionId": session_id,
            "greeting": greeting
        }
    except Exception as e:
        logger.error(f"❌ Chat init error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/message")
async def send_message(request: ChatMessageRequest):
    """Send a message to the chat agent."""
    try:
        if not agent:
            raise HTTPException(status_code=500, detail="Agent not initialized")
        
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        logger.info(f"💬 Processing message from session {request.sessionId}: {request.message[:50]}...")
        
        response = await agent.process_message(request.message)
        
        logger.info(f"✅ Response generated: {response[:50]}...")
        return {
            "response": response
        }
    except Exception as e:
        logger.error(f"❌ Message processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history for a session."""
    try:
        if not agent:
            raise HTTPException(status_code=500, detail="Agent not initialized")
        
        history = await agent.get_conversation_history()
        return {
            "sessionId": session_id,
            "history": history
        }
    except Exception as e:
        logger.error(f"❌ History retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/chat/session/{session_id}")
async def end_chat_session(session_id: str):
    """End a chat session."""
    try:
        if not agent:
            raise HTTPException(status_code=500, detail="Agent not initialized")
        
        goodbye = await agent.end_chat_session()
        logger.info(f"👋 Chat session ended: {session_id}")
        return {
            "message": goodbye,
            "sessionId": session_id
        }
    except Exception as e:
        logger.error(f"❌ Session end error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    logger.info(f"🚀 Starting Text Chat Agent API on {host}:{port}")
    
    uvicorn.run(
        "api_server:app",
        host=host,
        port=port,
        reload=True,
        log_level=log_level
    )
