# LiveKit Customer Support Voice Agent

A sophisticated real-time customer support voice agent built with LiveKit that provides natural, conversational AI interactions with complete e-commerce order management capabilities.

## Features

### 🎤 **Voice Interaction**

- **Real-time Conversation**: Natural, human-like voice interactions
- **Perfect Interruption Handling**: Agent stops talking instantly when you start speaking
- **High-Quality Audio**: Uses Deepgram for STT, ElevenLabs for TTS, OpenAI GPT-4 for responses
- **Noise Cancellation**: Background noise filtering for crystal-clear audio
- **Complete Sentence Processing**: Waits for complete queries before processing
- **Conversation Memory**: Persistent conversation history using Redis database
- **Session Management**: Remembers previous interactions and provides context-aware responses

### 🛒 **E-commerce Features**

- **Real Order Placement**: Place actual orders that update JSON database
- **Order Cancellation**: Cancel orders with automatic stock restoration
- **Product Search**: Search by category, name, brand, or features
- **Order Tracking**: Check order status and delivery information
- **Customer Management**: Full customer profile integration
- **Inventory Management**: Real-time stock tracking and updates

### 🎯 **Customer Support Capabilities**

1. **Customer Information Lookup** (by email, phone, or customer ID)
2. **Product Information & Search** (detailed product catalogs)
3. **Order Status & Tracking** (real-time order management)
4. **Order Placement** (complete e-commerce functionality)
5. **Order Cancellation** (with refund processing)
6. **General Product Queries** (returns, shipping, warranty info)
7. **Category-based Shopping** (browse by product categories)

## Setup

1. **Install Dependencies**:

   ```bash
   pip install -e .
   ```

2. **Configure Environment**:

   - Copy `env.example` to `.env`
   - Fill in your API keys:
     - `OPENAI_API_KEY` - For GPT-4 intelligent responses
     - `ELEVENLABS_API_KEY` - For natural voice synthesis
     - `DEEPGRAM_API_KEY` - For speech-to-text conversion
     - `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` - LiveKit credentials

3. **Run the Customer Support Agent**:
   ```bash
   python customer_support_agent.py console
   ```

## Example Usage

### 🛍️ **Order Placement**

```
User: "I want to order wireless bluetooth headphones, my customer ID is CUST001"
Agent: "🎉 Order placed successfully! Order ID: ORD005, Total: $89.99..."
```

### ❌ **Order Cancellation**

```
User: "Cancel order ORD005"
Agent: "✅ Order ORD005 cancelled! Refund of $89.99 will be processed..."
```

### 🔍 **Product Search**

```
User: "Show me electronics products"
Agent: "Here are our electronics products: 1. Wireless Headphones - $89.99..."
```

### 📋 **Order Lookup**

```
User: "Check my order ORD001"
Agent: "Order ORD001 - Delivered. Date: 2024-08-15, Total: $289.97..."
```

## File Structure

```
Live-kit/
├── customer_support_agent.py    # Main customer support voice agent
├── agent.py                     # Basic voice agent (for reference)
├── data/                        # JSON database files
│   ├── customers.json          # Customer profiles and information
│   ├── products.json           # Product catalog with live stock
│   └── orders.json             # Order database with real-time updates
├── env.example                 # Environment variables template
├── pyproject.toml             # Project dependencies and configuration
└── README.md                  # This file
```

## How It Works

### 🎯 **Real-time Order Management**

- **JSON Database**: All data stored in JSON files with real-time updates
- **Stock Management**: Automatic inventory tracking with order placement/cancellation
- **Order Processing**: Complete order lifecycle from placement to delivery tracking
- **Customer Validation**: Verifies customer existence before processing orders

### 🎤 **Advanced Voice Processing**

- **Query Buffering**: Collects speech fragments into complete sentences
- **Smart Classification**: Distinguishes between order placement, lookup, and cancellation
- **Pattern Recognition**: Extracts customer IDs, order IDs, and quantities from speech
- **Immediate Interruption**: Stops speaking instantly when user starts talking

### 🏗️ **Architecture**

- **CustomerSupportAgent**: Main agent class with e-commerce capabilities
- **DataManager**: Handles all JSON file operations and data persistence
- **Real-time Processing**: Immediate updates to orders and inventory
- **Error Handling**: Comprehensive validation and user-friendly error messages

## Technical Features

- **Live JSON Updates**: All changes immediately saved to database files
- **Stock Restoration**: Automatic inventory restoration on order cancellation
- **Order ID Generation**: Unique order IDs (ORD001, ORD002, etc.)
- **Customer Profile Integration**: Full customer information lookup
- **Multi-category Product Search**: Electronics, clothing, home, books, sports, beauty
- **Voice Activity Detection**: Smart detection of speech start/stop
- **Manual Turn Detection**: Better control over conversation flow

## Customization

You can customize the agent by:

- Changing the voice in ElevenLabs TTS configuration
- Modifying the system instructions
- Adjusting the LLM parameters (temperature, max_tokens)
- Adding custom tools and functions

## Requirements

- Python 3.10+
- LiveKit Cloud account
- API keys for OpenAI, ElevenLabs, and Deepgram
