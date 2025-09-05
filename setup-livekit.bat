@echo off
cls
echo ===============================================
echo        LiveKit Professional Setup
echo ===============================================
echo.

:: Check if Docker is running
echo [1/6] Checking Docker...
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Docker is not running. Please start Docker Desktop or Rancher Desktop first.
    echo.
    pause
    exit /b 1
)
echo ✅ Docker is running

:: Create Next.js environment file
echo [2/6] Creating Next.js environment...
if not exist "livekit-web\.env.local" (
    (
        echo # LiveKit Configuration for Local Development
        echo # These match the official LiveKit --dev mode settings
        echo NEXT_PUBLIC_LIVEKIT_URL=ws://localhost:7880
        echo NEXT_PUBLIC_LIVEKIT_API_KEY=devkey
        echo LIVEKIT_API_SECRET=secret
    ) > "livekit-web\.env.local"
    echo ✅ Created livekit-web\.env.local
) else (
    echo ℹ️  livekit-web\.env.local already exists
)

:: Create Python agent environment file
echo [3/6] Creating Python agent environment...
if not exist "Live-kit\.env" (
    (
        echo # OpenAI API Key ^(for GPT-4 responses^)
        echo OPENAI_API_KEY=your_openai_api_key_here
        echo.
        echo # ElevenLabs API Key ^(for natural voice synthesis^)
        echo ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
        echo.
        echo # Deepgram API Key ^(for speech-to-text^)
        echo DEEPGRAM_API_KEY=your_deepgram_api_key_here
        echo.
        echo # Redis URL for conversation history storage
        echo REDIS_URL=redis://localhost:6379
        echo.
        echo # LiveKit Configuration - Official Development Mode
        echo LIVEKIT_URL=ws://localhost:7880
        echo LIVEKIT_API_KEY=devkey
        echo LIVEKIT_API_SECRET=secret
        echo.
        echo # Session Configuration
        echo SESSION_TIMEOUT=3600
        echo MAX_CONVERSATION_HISTORY=50
    ) > "Live-kit\.env"
    echo ✅ Created Live-kit\.env
    echo ⚠️  Please update the API keys in Live-kit\.env before running your agent
) else (
    echo ℹ️  Live-kit\.env already exists
)

:: Build and start LiveKit services
echo [4/6] Building and starting LiveKit services...
echo This may take a few minutes the first time...
docker compose up --build -d
if %ERRORLEVEL% neq 0 (
    echo ❌ Failed to start Docker services
    pause
    exit /b 1
)

:: Wait for services to start
echo [5/6] Waiting for services to start...
timeout /t 15 /nobreak >nul

:: Check LiveKit health
echo [6/6] Checking service health...
curl -f http://localhost:7880/healthz >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo ✅ LiveKit server is healthy at ws://localhost:7880
) else (
    echo ⚠️  LiveKit server is starting up. Check logs with: docker compose logs livekit
)

:: Check Redis
docker exec livekit-redis redis-cli ping >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo ✅ Redis is running at localhost:6379
) else (
    echo ❌ Redis is not responding
)

echo.
echo ===============================================
echo       🎉 LiveKit Setup Complete!
echo ===============================================
echo.
echo LiveKit Configuration:
echo   • URL: ws://localhost:7880
echo   • API Key: devkey
echo   • API Secret: secret
echo   • Development Mode: Enabled
echo.
echo Next Steps:
echo   1. Update API keys in Live-kit\.env
echo   2. Start Python agent: cd Live-kit ^&^& python customer_support_agent.py dev
echo   3. Start Next.js app: cd livekit-web ^&^& npm run dev
echo   4. Open http://localhost:3000 in your browser
echo.
echo Useful Commands:
echo   • View logs: docker compose logs livekit -f
echo   • Stop services: docker compose down
echo   • Restart: docker compose restart
echo   • Check status: docker ps
echo.
pause
