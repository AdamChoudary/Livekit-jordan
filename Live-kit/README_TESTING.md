# Testing the Text Chat Agent

## Prerequisites

1. **Install dependencies:**

   ```bash
   pip install -e .
   ```

2. **Set up environment variables:**

   ```bash
   cp env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

3. **Get Gemini API Key:**
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Add it to your `.env` file

## Testing Methods

### 1. Interactive Chat Test

```bash
python test_chat.py
```

- Interactive terminal chat
- Type messages and get responses
- Type 'quit', 'exit', or 'bye' to end

### 2. Quick Test

```bash
python test_quick.py
```

- Automated test with predefined messages
- Tests basic functionality
- No user interaction required

### 3. Direct Python Test

```bash
python -c "
import asyncio
import sys
import os
sys.path.append('src')
from text_chat_agent import TextChatAgent

async def test():
    agent = TextChatAgent()
    greeting = await agent.start_chat_session('test_user')
    print(f'Agent: {greeting}')
    response = await agent.process_message('Hello!')
    print(f'Agent: {response}')

asyncio.run(test())
"
```

## Example Test Session

```
🤖 Text Chat Agent Test
==================================================
🚀 Initializing Text Chat Agent...
👋 Starting chat session...
Agent: Hello! I'm Sarah, your AI customer support assistant. How can I help you today?

💬 Chat with the agent! Type 'quit', 'exit', or 'bye' to end the conversation.
==================================================
You: What products do you have?
🤔 Agent is thinking...
Agent: We have a great selection of products! Here are some of our available items:

- Wireless Bluetooth Headphones (ID: PROD001) - $99.99
  Brand: TechSound | Category: Electronics
  Stock: 50 | Rating: 4.5/5
  Description: High-quality wireless headphones with noise cancellation

- Smart Fitness Watch (ID: PROD002) - $199.99
  Brand: FitTech | Category: Electronics
  Stock: 30 | Rating: 4.3/5
  Description: Advanced fitness tracking with heart rate monitoring

Which product interests you most?

You: quit
Agent: Thank you for chatting with us! Have a great day!
```

## Troubleshooting

### Common Issues

1. **"GEMINI_API_KEY not found"**

   - Make sure you have a `.env` file with your API key
   - Check that the key is valid

2. **"Module not found"**

   - Make sure you're in the correct directory
   - Install dependencies with `pip install -e .`

3. **"Redis connection error"**
   - Redis is optional for conversation history
   - The agent will work without Redis, just won't save conversation history

### Debug Mode

Set `LOG_LEVEL=DEBUG` in your `.env` file for more detailed logging.

## Test Scenarios

Try these test messages:

- "Hello!"
- "What products do you have?"
- "Tell me about wireless headphones"
- "I want to place an order"
- "What's my order status?"
- "I need to cancel an order"
- "Thank you!"
