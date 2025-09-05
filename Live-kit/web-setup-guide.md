# LiveKit Voice Agent Web Setup Guide

## Prerequisites

- Your existing customer support agent (`customer_support_agent.py`)
- Node.js and npm installed
- LiveKit Cloud account or self-hosted LiveKit server

## Step 1: Create Next.js Frontend

```bash
npx create-next-app@latest voice-agent-web
cd voice-agent-web
npm install @livekit/components-react livekit-client @livekit/agents
```

## Step 2: Environment Variables

Create `.env.local` in your Next.js project:

```env
NEXT_PUBLIC_LIVEKIT_URL=wss://your-livekit-url
NEXT_PUBLIC_LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
```

## Step 3: Create Voice Chat Component

Create `components/VoiceChat.tsx`:

```tsx
"use client";

import { useVoiceAssistant } from "@livekit/components-react";
import { useState } from "react";

export default function VoiceChat() {
  const [connectionDetails, setConnectionDetails] = useState(null);

  const { state, audioTrack, agentState } = useVoiceAssistant({
    serverUrl: process.env.NEXT_PUBLIC_LIVEKIT_URL!,
    token: connectionDetails?.accessToken,
  });

  const connectToAgent = async () => {
    const response = await fetch("/api/connection-details", {
      method: "POST",
    });
    const details = await response.json();
    setConnectionDetails(details);
  };

  return (
    <div className="voice-chat-container">
      <h1>Customer Support Voice Agent</h1>

      {!connectionDetails ? (
        <button onClick={connectToAgent} className="connect-btn">
          Start Voice Chat
        </button>
      ) : (
        <div className="chat-interface">
          <div className="status">
            Status: {state} | Agent: {agentState}
          </div>

          <div className="audio-controls">
            {audioTrack && (
              <audio
                ref={(el) => {
                  if (el) el.srcObject = new MediaStream([audioTrack]);
                }}
                autoPlay
              />
            )}
          </div>

          <div className="chat-history">
            {/* Chat messages will appear here */}
          </div>
        </div>
      )}
    </div>
  );
}
```

## Step 4: Create API Route for Connection

Create `app/api/connection-details/route.ts`:

```typescript
import { AccessToken } from "livekit-server-sdk";

export async function POST() {
  const roomName = `voice-chat-${Math.random().toString(36).substring(7)}`;
  const participantName = `user-${Math.random().toString(36).substring(7)}`;

  const token = new AccessToken(
    process.env.NEXT_PUBLIC_LIVEKIT_API_KEY!,
    process.env.LIVEKIT_API_SECRET!,
    {
      identity: participantName,
      ttl: "10m",
    }
  );

  token.addGrant({
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canSubscribe: true,
  });

  return Response.json({
    accessToken: await token.toJwt(),
    url: process.env.NEXT_PUBLIC_LIVEKIT_URL!,
    roomName,
  });
}
```

## Step 5: Update Your Agent for Web

Modify your `customer_support_agent.py` to work with web connections:

```python
# Add to your entrypoint function
async def entrypoint(ctx: agents.JobContext):
    # Connect to room first
    await ctx.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)

    # Wait for participant
    participant = await ctx.wait_for_participant()
    logger.info(f"Participant {participant.identity} joined")

    # Rest of your existing code...
```

## Step 6: Run Everything

1. **Start your LiveKit agent:**

```bash
python customer_support_agent.py dev
```

2. **Start your Next.js app:**

```bash
npm run dev
```

3. **Access your web interface:**
   Open `http://localhost:3000`

## Architecture Overview

```
User Browser → Next.js Frontend → LiveKit Server → Your Python Agent
     ↑                                                      ↓
     ←─────────── Voice/Audio Response ←─────────────────────
```

## Key Features Your Web Interface Will Have:

✅ **Real-time Voice Chat** - Direct voice communication with your agent
✅ **Visual Chat History** - See conversation transcripts
✅ **Connection Status** - Know when agent is listening/speaking
✅ **Responsive Design** - Works on desktop and mobile
✅ **All Your Agent Features** - Customer support, orders, products, etc.

## Next Steps:

1. Style your interface with Tailwind CSS
2. Add chat message display
3. Implement typing indicators
4. Add error handling
5. Deploy to production

Would you like me to help you implement any specific part of this setup?
