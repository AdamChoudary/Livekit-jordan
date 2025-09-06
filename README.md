# LiveKit Voice Agent Project

A sophisticated real-time voice-based customer support system with e-commerce capabilities.

## Project Structure

```
Livekit-jordan/
├── Live-kit/                    # Python Voice Agent & Backend
│   ├── customer_support_agent.py    # Main AI voice agent
│   ├── conversation_manager.py      # Redis conversation management
│   ├── agent.py                     # Basic voice agent
│   ├── data/                        # JSON databases (customers, products, orders)
│   ├── docker-compose.yml           # Docker services configuration
│   ├── Dockerfile.livekit           # Custom LiveKit server image
│   ├── livekit.yaml                 # LiveKit server configuration
│   ├── pyproject.toml               # Python dependencies
│   └── README.md                    # Agent documentation
│
└── livekit-web/                  # Next.js Frontend
    ├── src/
    │   ├── app/                   # Next.js app router
    │   └── components/            # React components
    ├── package.json               # Frontend dependencies
    └── README.md                  # Frontend documentation
```

## Quick Start

1. **Start the LiveKit server:**

   ```bash
   cd Live-kit
   docker-compose up --build -d
   ```

2. **Start the Python agent:**

   ```bash
   cd Live-kit
   python customer_support_agent.py dev
   ```

3. **Start the web frontend:**

   ```bash
   cd livekit-web
   npm run dev
   ```

4. **Access the application:**
   - Open `http://localhost:3000` in your browser

## Features

- 🎤 **Real-time Voice Chat** with natural interruption handling
- 🛒 **E-commerce Integration** - Place, track, and cancel orders
- 📦 **Product Search** across multiple categories
- 👤 **Customer Management** with profile creation and lookup
- 💬 **Conversation Memory** using Redis for persistent sessions
- 🤖 **AI-Powered** using OpenAI GPT-4, Deepgram STT/TTS

## Documentation

- [Live-kit/README.md](Live-kit/README.md) - Detailed agent documentation
- [Live-kit/DOCKER-SETUP.md](Live-kit/DOCKER-SETUP.md) - Docker setup guide
- [livekit-web/README.md](livekit-web/README.md) - Frontend documentation

## Technology Stack

- **Backend**: Python 3.10+, LiveKit Agents, OpenAI GPT-4, Deepgram
- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS
- **Infrastructure**: Docker, Redis, LiveKit Cloud
