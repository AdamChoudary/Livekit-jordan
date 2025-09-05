import asyncio
import logging
import os
from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    openai,
    deepgram,
    elevenlabs,
    noise_cancellation,
    silero,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealtimeVoiceAgent(Agent):
    """
    A real-time voice agent with proper interruption handling.
    This agent can be interrupted mid-conversation and will respond naturally.
    """
    
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a helpful, conversational AI assistant with real-time interruption capabilities. "
                "IMPORTANT BEHAVIOR: "
                "- You can be interrupted at ANY time while speaking - when this happens, STOP immediately and listen "
                "- When interrupted, acknowledge the interruption naturally and respond to the new input "
                "- Keep responses concise but informative (2-3 sentences max) "
                "- Always be friendly, helpful, and responsive "
                "- When asked about Pakistan, provide detailed information about its history, culture, and formation "
                "- Answer all questions thoroughly but concisely "
                "- If interrupted while answering, continue from where you left off or address the new question "
            )
        )
        self.last_processed_input = ""

    async def on_enter(self) -> None:
        """Called when the agent is first activated."""
        logger.info("RealtimeVoiceAgent activated")
        # Use session.say() for voice output
        await self.session.say("Hello! I'm your AI assistant. I can hear you and I'm ready to help with anything you need. Please speak to me!")

    async def on_user_turn_completed(self, chat_ctx, new_message) -> None:
        """Called when user completes a turn - generate intelligent response."""
        if not new_message.text_content or len(new_message.text_content) == 0:
            logger.info("Ignoring empty user turn")
            return
        
        user_text = new_message.text_content.strip()
        if user_text == self.last_processed_input:
            logger.info("Skipping duplicate input")
            return
            
        self.last_processed_input = user_text
        logger.info(f"Processing user question: {user_text}")
        
        # Use generate_reply to get an intelligent LLM response
        await self.session.generate_reply(user_input=user_text)
    
    async def on_user_start_speaking(self) -> None:
        """Called when user starts speaking - INTERRUPT the agent immediately."""
        logger.info("🎤 IMMEDIATE INTERRUPTION - User speaking!")
        # Use the most direct interruption method
        if hasattr(self.session, 'interrupt'):
            await self.session.interrupt()
        
    async def on_user_stop_speaking(self) -> None:
        """Called when user stops speaking - ready to respond."""
        logger.info("🔇 User stopped - processing input")
        # Let the session handle the response automatically
    
    async def on_agent_start_speaking(self) -> None:
        """Called when agent starts speaking."""
        logger.info("🗣️ Agent started speaking")
        
    async def on_agent_stop_speaking(self) -> None:
        """Called when agent stops speaking."""
        logger.info("🔇 Agent stopped speaking")
    
    async def process_transcript(self, transcript_text):
        """Process transcript and generate intelligent response."""
        if not transcript_text or transcript_text.strip() == self.last_processed_input:
            return
            
        self.last_processed_input = transcript_text.strip()
        logger.info(f"Processing transcript: {transcript_text}")
        
        # Generate intelligent response
        await self.session.generate_reply(user_input=transcript_text)


async def entrypoint(ctx: agents.JobContext):
    """
    Main entrypoint for the real-time voice agent.
    Based on the working TypeScript examples.
    """
    logger.info("Starting real-time voice agent...")
    
    # Connect to the room first
    await ctx.connect()
    
    # Create the voice agent
    agent = RealtimeVoiceAgent()
    
    # Configure the agent session with optimal interruption settings
    session = AgentSession(
        # Speech-to-Text: Deepgram for accurate transcription
        stt=deepgram.STT(api_key=os.getenv("DEEPGRAM_API_KEY")),
        
        # Large Language Model: OpenAI GPT-4 for intelligent responses
        llm=openai.LLM(api_key=os.getenv("OPENAI_API_KEY")),
        
        # Text-to-Speech: ElevenLabs for natural voice
        tts=elevenlabs.TTS(api_key=os.getenv("ELEVENLABS_API_KEY")),
        
        # Voice Activity Detection: Silero for detecting when user speaks
        vad=silero.VAD.load(),
        
        # Turn Detection: Use server-side turn detection for immediate interruption
        turn_detection="server_vad",
    )

    # Start the session
    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(), 
        ),
    )

    # Register RPC methods for manual turn control (like in the TypeScript example)
    async def start_turn():
        session.interrupt()
        session.clear_user_turn()
        return 'ok'

    async def end_turn():
        session.commit_user_turn()
        return 'ok'

    async def cancel_turn():
        session.clear_user_turn()
        return 'ok'

    ctx.room.local_participant.register_rpc_method('start_turn', start_turn)
    ctx.room.local_participant.register_rpc_method('end_turn', end_turn)
    ctx.room.local_participant.register_rpc_method('cancel_turn', cancel_turn)
    
    # Simple and direct interruption setup
    logger.info("Setting up immediate interruption system...")
    
    # Minimal event setup for basic functionality
    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        logger.info(f"Participant connected: {participant.identity}")
    
    @ctx.room.on("participant_disconnected") 
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        logger.info(f"Participant disconnected: {participant.identity}")
    
    # Set up proper turn management for immediate interruption and response
    async def ensure_turn_processing():
        """Ensure user turns are processed immediately."""
        await asyncio.sleep(2)  # Wait for session to be ready
        while True:
            try:
                # Commit user turns to ensure they're processed
                session.commit_user_turn()
                await asyncio.sleep(1)  # Check every second
            except Exception as e:
                logger.debug(f"Turn processing error: {e}")
                await asyncio.sleep(1)
    
    # Start turn processing
    asyncio.create_task(ensure_turn_processing())
    
    logger.info("✅ Using LiveKit's native interruption system")

    # Generate initial greeting using session.say()
    await session.say("Hello, how can I help you today?")
    
    # Simple approach: Remove the periodic generic responses and let the agent respond naturally
    # The key is to ensure the session processes user input correctly
    
    # Force the session to start processing user input immediately
    await asyncio.sleep(1)  # Give the session time to initialize
    
    # Enable automatic response generation
    session._auto_generate_replies = True  # Enable automatic replies if available
    
    # Keep the agent running
    try:
        await asyncio.Event().wait()  # Run indefinitely
    except KeyboardInterrupt:
        logger.info("Shutting down voice agent...")


if __name__ == "__main__":
    # Run the agent with CLI
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))