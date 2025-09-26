# Chat Implementation Guide

## Overview

This implementation adds a `/chat` route to the livekit-web application that allows users to chat with the text-based AI agent. The system includes:

- **Frontend**: Next.js chat interface with markdown rendering
- **Backend**: FastAPI server for the Python text chat agent
- **Docker**: Containerized deployment setup

## Architecture

```
User → Next.js Frontend (/chat) → Next.js API Routes → FastAPI Server → Text Chat Agent
```

## Files Created/Modified

### Frontend (livekit-web)

- `package.json` - Added react-markdown and remark-gfm dependencies
- `src/app/chat/page.tsx` - Chat interface with markdown rendering
- `src/app/api/chat/init/route.ts` - Initialize chat session
- `src/app/api/chat/message/route.ts` - Send messages to agent

### Backend (Live-kit)

- `pyproject.toml` - Added FastAPI and uvicorn dependencies
- `src/api_server.py` - FastAPI server for the text chat agent
- `Dockerfile.api` - Docker configuration for API server
- `docker-compose.api.yml` - Docker Compose setup with Redis

## Setup Instructions

### 1. Install Dependencies

#### Frontend

```bash
cd livekit-web
npm install
```

#### Backend

```bash
cd Live-kit
pip install -e .
```

### 2. Environment Setup

Create `.env` file in Live-kit directory:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
REDIS_URL=redis://localhost:6379/0
SESSION_TIMEOUT=3600
MAX_CONVERSATION_HISTORY=50
```

### 3. Running the System

#### Option A: Docker (Recommended)

```bash
cd Live-kit
docker-compose -f docker-compose.api.yml up -d
```

#### Option B: Manual Setup

```bash
# Terminal 1: Start Redis
docker run -d -p 6379:6379 redis:alpine

# Terminal 2: Start Python API
cd Live-kit
python src/api_server.py

# Terminal 3: Start Next.js
cd livekit-web
npm run dev
```

### 4. Access the Chat Interface

Visit: `http://localhost:3000/chat`

## API Endpoints

### Python FastAPI Server (Port 8000)

- `GET /` - Health check
- `GET /health` - Detailed health check
- `POST /api/chat/init` - Initialize chat session
- `POST /api/chat/message` - Send message to agent
- `GET /api/chat/history/{session_id}` - Get chat history
- `DELETE /api/chat/session/{session_id}` - End chat session

### Next.js API Routes (Port 3000)

- `POST /api/chat/init` - Proxy to Python API
- `POST /api/chat/message` - Proxy to Python API

## Features

### Chat Interface

- ✅ Real-time chat with typing indicators
- ✅ Markdown rendering for AI responses
- ✅ Message history with timestamps
- ✅ Responsive design with dark mode
- ✅ Auto-scroll to latest messages
- ✅ Loading states and error handling

### Markdown Support

- ✅ **Bold** and _italic_ text
- ✅ Lists (ordered and unordered)
- ✅ Code blocks and inline code
- ✅ Blockquotes
- ✅ Links and other GFM features

### Backend Features

- ✅ Session management
- ✅ Conversation history with Redis
- ✅ Error handling and logging
- ✅ Health checks
- ✅ CORS support
- ✅ Docker containerization

## Testing

### Test the API Directly

```bash
# Initialize chat
curl -X POST http://localhost:8000/api/chat/init

# Send message
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "sessionId": "your-session-id"}'
```

### Test the Frontend

1. Open `http://localhost:3000/chat`
2. Type a message and press Enter
3. Verify markdown rendering works

## Troubleshooting

### Common Issues

1. **"Failed to initialize chat"**

   - Check if Python API is running on port 8000
   - Verify GEMINI_API_KEY is set correctly

2. **"Module not found" errors**

   - Run `pip install -e .` in Live-kit directory
   - Check Python path and virtual environment

3. **Redis connection errors**

   - Ensure Redis is running on port 6379
   - Check REDIS_URL in environment variables

4. **CORS errors**
   - Verify Next.js is running on port 3000
   - Check CORS settings in api_server.py

### Debug Mode

Set `LOG_LEVEL=debug` in your `.env` file for detailed logging.

## Production Deployment

### Docker Compose

```bash
docker-compose -f docker-compose.api.yml up -d
```

### Environment Variables for Production

```bash
GEMINI_API_KEY=your_production_key
REDIS_URL=redis://your-redis-server:6379/0
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=info
```

## Security Considerations

- ✅ CORS configured for specific origins
- ✅ Input validation on API endpoints
- ✅ Non-root user in Docker container
- ✅ Health checks for monitoring
- ⚠️ Add authentication for production use
- ⚠️ Add rate limiting for API endpoints
- ⚠️ Use HTTPS in production

## Performance

- ✅ Redis for fast conversation storage
- ✅ Async/await for non-blocking operations
- ✅ Connection pooling for database
- ✅ Efficient markdown rendering
- ⚠️ Consider adding caching for frequent queries
- ⚠️ Monitor memory usage with large conversations
