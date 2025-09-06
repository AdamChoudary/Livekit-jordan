import asyncio
import logging
import os
from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    openai,
    deepgram,
    silero,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CustomerSupportAgent(Agent):
    """
    Clean, working Customer Support Agent using proper LiveKit methods.
    """
    
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are Sarah, a friendly and professional customer support agent. "
                "Keep responses short, natural, and helpful (1-2 sentences). "
                "Be conversational and warm. "
                "You can be interrupted at any time - when this happens, stop immediately and listen. "
                "Ask clarifying questions when needed. "
                "Help with product questions, orders, and general support."
            )
        )
        self.last_processed_input = ""

    async def on_enter(self) -> None:
        """Called when the agent is first activated."""
        logger.info("Customer Support Agent activated")
        
        # Use session.say() for voice output - this is the correct method
        await self.session.say(
            "Hello! I'm Sarah from customer support. "
            "How can I help you today?"
        )

    async def on_user_turn_completed(self, chat_ctx, new_message) -> None:
        """Process user input using the correct LiveKit method."""
        if not new_message.text_content or len(new_message.text_content) == 0:
            return

        user_text = new_message.text_content.strip()
        if not user_text or user_text == self.last_processed_input:
            return

        self.last_processed_input = user_text
        logger.info(f"🎤 Customer: {user_text}")

        # Use the correct LiveKit method for generating responses
        # This handles LLM calls, context, and TTS automatically
        await self.session.generate_reply(user_input=user_text)

    async def on_user_start_speaking(self) -> None:
        """Called when user starts speaking - handle interruption."""
        logger.info("🎤 Customer interrupting - listening now!")
        # The session handles interruption automatically

    async def on_user_stop_speaking(self) -> None:
        """Called when user stops speaking."""
        logger.info("🔇 Customer stopped speaking")

    async def on_agent_start_speaking(self) -> None:
        """Called when agent starts speaking."""
        logger.info("🗣️ Agent started speaking")

    async def on_agent_stop_speaking(self) -> None:
        """Called when agent stops speaking."""
        logger.info("🔇 Agent finished speaking")


async def entrypoint(ctx: agents.JobContext):
    """
    Clean entrypoint for the customer support agent.
    """
    logger.info("Starting Customer Support Agent...")
    
    # Connect to the room
    await ctx.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)
    
    # Create the agent
    agent = CustomerSupportAgent()
    
    # Configure the agent session with optimal settings for performance
    session = AgentSession(
        # Speech-to-Text: Deepgram
        stt=deepgram.STT(api_key=os.getenv("DEEPGRAM_API_KEY")),
        
        # Large Language Model: OpenAI GPT-4
        llm=openai.LLM(api_key=os.getenv("OPENAI_API_KEY")),
        
        # Text-to-Speech: Deepgram with natural voice
        tts=deepgram.TTS(
            model="aura-luna-en",
            api_key=os.getenv("DEEPGRAM_API_KEY")
        ),
        
        # Voice Activity Detection: Optimized for performance
        vad=silero.VAD.load(
            min_speech_duration=0.3,    # Balanced detection (300ms)
            min_silence_duration=0.8,   # Longer silence to reduce false triggers (800ms)
        ),
        
        # Turn Detection: Use server VAD for better performance
        turn_detection="server_vad",
    )

    # Start the session with minimal room input options
    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(),  # Minimal settings for best performance
    )

    logger.info("✅ Customer Support Agent ready!")

    # Simple event handlers
    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        logger.info(f"Customer connected: {participant.identity}")
    
    @ctx.room.on("participant_disconnected") 
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        logger.info(f"Customer disconnected: {participant.identity}")

    # Keep running
    try:
        logger.info("✅ Agent running and ready for customers!")
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Agent error: {e}")
    finally:
        logger.info("Agent shutting down...")


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
