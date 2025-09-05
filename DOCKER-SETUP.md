# LiveKit Docker Setup Guide

This guide will help you run LiveKit on your local server using Docker, connected to a Next.js frontend for voice chat functionality.

## 🚀 Quick Start

### Prerequisites

- Docker Desktop installed and running
- Node.js and npm installed
- Python 3.10+ installed

### 1. Start LiveKit Server

**Windows Users:**

```bash
# Run the batch file
start-livekit-local.bat

# OR run the PowerShell script
.\start-livekit-local.ps1
```

**Linux/Mac Users:**

```bash
# Make sure Docker is running
docker-compose up --build -d
```

### 2. Verify Services

After running the startup script, you should see:

- ✅ LiveKit server running at `ws://localhost:7880`
- ✅ Redis running at `localhost:6379`

## 📁 File Structure

```
📦 Your Project
├── 🐳 Docker Configuration
│   ├── docker-compose.yml        # Docker services definition
│   ├── Dockerfile.livekit         # Custom LiveKit image
│   ├── livekit.yaml              # LiveKit server configuration
│   └── start-livekit.sh          # Container startup script
│
├── 🖥️ Frontend (Next.js)
│   ├── livekit-web/
│   │   ├── src/
│   │   │   ├── app/api/livekit/   # Token generation API
│   │   │   └── components/        # Voice chat components
│   │   └── .env.local             # Frontend environment variables
│
├── 🤖 Python Agent
│   ├── Live-kit/
│   │   ├── customer_support_agent.py
│   │   └── .env                   # Agent environment variables
│
└── 🚀 Startup Scripts
    ├── start-livekit-local.bat    # Windows batch file
    └── start-livekit-local.ps1    # PowerShell script
```

## 🔧 Manual Setup

### 1. Build and Run LiveKit Server

```bash
# Build the custom LiveKit image
docker build -f Dockerfile.livekit -t livekit-jordan:local .

# Start services
docker-compose up -d

# Check logs
docker-compose logs livekit
```

### 2. Configure Environment Variables

**Frontend (.env.local in livekit-web/):**

```env
NEXT_PUBLIC_LIVEKIT_URL=ws://localhost:7880
NEXT_PUBLIC_LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=devsecret
```

**Python Agent (.env in Live-kit/):**

```env
OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
DEEPGRAM_API_KEY=your_deepgram_api_key_here
REDIS_URL=redis://localhost:6379
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=devsecret
```

### 3. Start the Applications

**Terminal 1 - Python Agent:**

```bash
cd Live-kit
python customer_support_agent.py dev
```

**Terminal 2 - Next.js Frontend:**

```bash
cd livekit-web
npm run dev
```

**Terminal 3 - Access the Application:**

- Open `http://localhost:3000` in your browser

## 🔍 Verification & Testing

### 1. Check LiveKit Server

```bash
curl http://localhost:7880/healthz
# Should return: OK
```

### 2. Check Container Status

```bash
docker ps
# You should see livekit-server and livekit-redis containers running
```

### 3. View Logs

```bash
# LiveKit server logs
docker-compose logs livekit

# Redis logs
docker-compose logs redis

# Follow logs in real-time
docker-compose logs -f livekit
```

### 4. Test Voice Chat

1. Go to `http://localhost:3000`
2. Enter your name
3. Click "🎤 Start Voice Chat"
4. You should see connection status indicators
5. Speak to test voice interaction

## 🛠️ Docker Configuration Details

### Custom Dockerfile Features

- **Security**: Runs as non-root user (`livekit`)
- **Logging**: Comprehensive startup logs
- **Health Checks**: Built-in health monitoring
- **Debugging**: Includes curl and netcat for troubleshooting
- **Configuration**: Properly configured paths and permissions

### Exposed Ports

- `7880`: LiveKit API and WebSocket connections
- `7881`: TURN/TLS for secure connections
- `7882/udp`: UDP for media streaming
- `6379`: Redis for session storage

### Volumes and Data

- Configuration: `/etc/livekit/livekit.yaml`
- Data Directory: `/var/lib/livekit`
- Log Directory: `/var/log/livekit`

## 🐛 Troubleshooting

### Common Issues

**Docker not running:**

```bash
# Start Docker Desktop or Docker daemon
# Windows: Open Docker Desktop application
# Linux: sudo systemctl start docker
```

**Port conflicts:**

```bash
# Check what's using port 7880
netstat -an | findstr 7880  # Windows
lsof -i :7880               # Linux/Mac

# Kill processes if needed
```

**LiveKit server not responding:**

```bash
# Check container logs
docker-compose logs livekit

# Restart container
docker-compose restart livekit

# Rebuild and restart
docker-compose up --build -d
```

**Redis connection issues:**

```bash
# Check Redis container
docker exec livekit-redis redis-cli ping

# Should return: PONG
```

### Debug Mode

Enable debug logging by modifying `livekit.yaml`:

```yaml
logging:
  level: debug # Change from 'info' to 'debug'
```

Then rebuild:

```bash
docker-compose up --build -d
```

## 🔒 Production Considerations

**⚠️ This setup is for LOCAL DEVELOPMENT ONLY**

For production deployment:

1. Change the API keys in `livekit.yaml`
2. Use proper SSL certificates
3. Configure external access and firewall rules
4. Use a production-ready Redis instance
5. Enable authentication and authorization
6. Monitor performance and logs

## 📞 Support

If you encounter issues:

1. Check the Docker logs: `docker-compose logs livekit`
2. Verify all environment variables are set correctly
3. Ensure Docker has sufficient resources allocated
4. Check that no other services are using the required ports

## 🎯 Next Steps

Once everything is running:

1. Customize the voice agent behavior in `customer_support_agent.py`
2. Modify the frontend UI in `livekit-web/src/components/VoiceChat.tsx`
3. Add your own API keys for production-quality voice services
4. Integrate with your existing customer database and systems
