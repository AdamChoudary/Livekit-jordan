#!/usr/bin/env python3
"""
Simple test script for the Text Chat Agent.
Run this to test the agent in your terminal.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from text_chat_agent import TextChatAgent

# Load environment variables
load_dotenv()

async def main():
    """Test the text chat agent."""
    print("🤖 Text Chat Agent Test")
    print("=" * 50)
    
    # Check if Gemini API key is set
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY not found in environment variables.")
        print("Please set your Gemini API key in the .env file.")
        print("Example: GEMINI_API_KEY=your_api_key_here")
        return
    
    # Initialize the agent
    print("🚀 Initializing Text Chat Agent...")
    agent = TextChatAgent()
    
    # Start a chat session
    print("👋 Starting chat session...")
    greeting = await agent.start_chat_session("test_user")
    print(f"Agent: {greeting}")
    print()
    
    # Interactive chat loop
    print("💬 Chat with the agent! Type 'quit', 'exit', or 'bye' to end the conversation.")
    print("=" * 50)
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                break
            
            # Skip empty input
            if not user_input:
                continue
            
            # Process the message
            print("🤔 Agent is thinking...")
            response = await agent.process_message(user_input)
            print(f"Agent: {response}")
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Please try again.")
            print()
    
    # End the session
    goodbye = await agent.end_chat_session()
    print(f"Agent: {goodbye}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
