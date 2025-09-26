#!/usr/bin/env python3
"""
Quick test script for the Text Chat Agent.
Tests basic functionality without interactive chat.
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

async def quick_test():
    """Quick test of the text chat agent."""
    print("🧪 Quick Test - Text Chat Agent")
    print("=" * 40)
    
    # Check if Gemini API key is set
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY not found in environment variables.")
        print("Please set your Gemini API key in the .env file.")
        return
    
    # Initialize the agent
    print("🚀 Initializing agent...")
    agent = TextChatAgent()
    
    # Start a chat session
    print("👋 Starting chat session...")
    greeting = await agent.start_chat_session("test_user")
    print(f"Agent: {greeting}")
    print()
    
    # Test messages
    test_messages = [
        "Hello!",
        "What products do you have?",
        "Tell me about wireless headphones",
        "I want to place an order",
        "Thank you!"
    ]
    
    print("📝 Running test messages...")
    print("=" * 40)
    
    for i, message in enumerate(test_messages, 1):
        print(f"Test {i}: {message}")
        print("🤔 Agent is thinking...")
        
        try:
            response = await agent.process_message(message)
            print(f"Agent: {response}")
            print()
        except Exception as e:
            print(f"❌ Error: {e}")
            print()
    
    # End the session
    goodbye = await agent.end_chat_session()
    print(f"Agent: {goodbye}")
    print("\n✅ Quick test completed!")

if __name__ == "__main__":
    try:
        asyncio.run(quick_test())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
