#!/bin/bash
set -e

echo "🚀 Starting LiveKit Server..."
echo "📊 Configuration: /etc/livekit.yaml"
echo "🌐 Server will be available at ws://localhost:7880"
echo "🔑 API Key: devkey"
echo ""

# Check if configuration file exists
if [ ! -f "/etc/livekit.yaml" ]; then
    echo "❌ Configuration file not found at /etc/livekit.yaml"
    exit 1
fi

echo "✅ Configuration file found"
echo "🎯 Starting LiveKit server with the following settings:"
echo "   - Port: 7880"
echo "   - Bind Address: 0.0.0.0"
echo "   - Development Mode: Enabled"
echo ""

# Start LiveKit server
exec livekit-server --config /etc/livekit.yaml --bind 0.0.0.0