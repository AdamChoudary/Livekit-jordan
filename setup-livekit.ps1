# LiveKit Professional Setup Script (PowerShell)

Clear-Host
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "        LiveKit Professional Setup" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Function to create file if it doesn't exist
function New-FileIfNotExists {
    param($Path, $Content)
    if (-not (Test-Path $Path)) {
        $Content | Out-File -FilePath $Path -Encoding UTF8 -NoNewline
        return $true
    }
    return $false
}

# [1/6] Check if Docker is running
Write-Host "[1/6] Checking Docker..." -ForegroundColor Yellow
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop or Rancher Desktop first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# [2/6] Create Next.js environment file
Write-Host "[2/6] Creating Next.js environment..." -ForegroundColor Yellow
$nextEnvContent = @"
# LiveKit Configuration for Local Development
# These match the official LiveKit --dev mode settings
NEXT_PUBLIC_LIVEKIT_URL=ws://localhost:7880
NEXT_PUBLIC_LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
"@

if (New-FileIfNotExists "livekit-web\.env.local" $nextEnvContent) {
    Write-Host "✅ Created livekit-web\.env.local" -ForegroundColor Green
} else {
    Write-Host "ℹ️  livekit-web\.env.local already exists" -ForegroundColor Blue
}

# [3/6] Create Python agent environment file
Write-Host "[3/6] Creating Python agent environment..." -ForegroundColor Yellow
$pythonEnvContent = @"
# OpenAI API Key (for GPT-4 responses)
OPENAI_API_KEY=your_openai_api_key_here

# ElevenLabs API Key (for natural voice synthesis)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Deepgram API Key (for speech-to-text)
DEEPGRAM_API_KEY=your_deepgram_api_key_here

# Redis URL for conversation history storage
REDIS_URL=redis://localhost:6379

# LiveKit Configuration - Official Development Mode
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret

# Session Configuration
SESSION_TIMEOUT=3600
MAX_CONVERSATION_HISTORY=50
"@

if (New-FileIfNotExists "Live-kit\.env" $pythonEnvContent) {
    Write-Host "✅ Created Live-kit\.env" -ForegroundColor Green
    Write-Host "⚠️  Please update the API keys in Live-kit\.env before running your agent" -ForegroundColor Yellow
} else {
    Write-Host "ℹ️  Live-kit\.env already exists" -ForegroundColor Blue
}

# [4/6] Build and start LiveKit services
Write-Host "[4/6] Building and starting LiveKit services..." -ForegroundColor Yellow
Write-Host "This may take a few minutes the first time..." -ForegroundColor Gray
$buildResult = docker compose up --build -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start Docker services" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# [5/6] Wait for services to start
Write-Host "[5/6] Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# [6/6] Check service health
Write-Host "[6/6] Checking service health..." -ForegroundColor Yellow

# Check LiveKit health
try {
    Invoke-RestMethod -Uri "http://localhost:7880/healthz" -TimeoutSec 5 | Out-Null
    Write-Host "✅ LiveKit server is healthy at ws://localhost:7880" -ForegroundColor Green
} catch {
    Write-Host "⚠️  LiveKit server is starting up. Check logs with: docker compose logs livekit" -ForegroundColor Yellow
}

# Check Redis
try {
    docker exec livekit-redis redis-cli ping | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Redis is running at localhost:6379" -ForegroundColor Green
    } else {
        Write-Host "❌ Redis is not responding" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Redis check failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "       🎉 LiveKit Setup Complete!" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "LiveKit Configuration:" -ForegroundColor White
Write-Host "  • URL: ws://localhost:7880" -ForegroundColor Gray
Write-Host "  • API Key: devkey" -ForegroundColor Gray
Write-Host "  • API Secret: secret" -ForegroundColor Gray
Write-Host "  • Development Mode: Enabled" -ForegroundColor Gray
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor White
Write-Host "  1. Update API keys in Live-kit\.env" -ForegroundColor Gray
Write-Host "  2. Start Python agent: " -NoNewline -ForegroundColor Gray
Write-Host "cd Live-kit; python customer_support_agent.py dev" -ForegroundColor Yellow
Write-Host "  3. Start Next.js app: " -NoNewline -ForegroundColor Gray
Write-Host "cd livekit-web; npm run dev" -ForegroundColor Yellow
Write-Host "  4. Open " -NoNewline -ForegroundColor Gray
Write-Host "http://localhost:3000" -ForegroundColor Cyan -NoNewline
Write-Host " in your browser" -ForegroundColor Gray
Write-Host ""
Write-Host "Useful Commands:" -ForegroundColor White
Write-Host "  • View logs: " -NoNewline -ForegroundColor Gray
Write-Host "docker compose logs livekit -f" -ForegroundColor Yellow
Write-Host "  • Stop services: " -NoNewline -ForegroundColor Gray
Write-Host "docker compose down" -ForegroundColor Yellow
Write-Host "  • Restart: " -NoNewline -ForegroundColor Gray
Write-Host "docker compose restart" -ForegroundColor Yellow
Write-Host "  • Check status: " -NoNewline -ForegroundColor Gray
Write-Host "docker ps" -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to continue"
