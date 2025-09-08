import { AccessToken } from "livekit-server-sdk";
import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const { participantName } = await request.json();

    // Generate a unique room name
    const roomName = `voice-chat-${Math.random().toString(36).substring(7)}`;
    const identity =
      participantName || `user-${Math.random().toString(36).substring(7)}`;

    // Get environment variables
    const livekitUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL;
    const apiKey = process.env.NEXT_PUBLIC_LIVEKIT_API_KEY;
    const apiSecret = process.env.LIVEKIT_API_SECRET;

    // Better error reporting for missing environment variables
    const missing = [];
    if (!livekitUrl) missing.push("NEXT_PUBLIC_LIVEKIT_URL");
    if (!apiKey) missing.push("NEXT_PUBLIC_LIVEKIT_API_KEY");
    if (!apiSecret) missing.push("LIVEKIT_API_SECRET");

    if (missing.length > 0) {
      console.error("Missing environment variables:", missing);
      return NextResponse.json(
        {
          error: "LiveKit configuration missing",
          details: `Missing environment variables: ${missing.join(", ")}`,
          hint: "Create .env.local file with required LiveKit configuration",
        },
        { status: 500 }
      );
    }

    console.log(
      `Creating LiveKit token for room: ${roomName}, identity: ${identity}`
    );

    // Create access token
    const token = new AccessToken(apiKey, apiSecret, {
      identity,
      ttl: "10m", // 10 minutes
    });

    // Add grants for the participant
    token.addGrant({
      room: roomName,
      roomJoin: true,
      canPublish: true,
      canSubscribe: true,
      canPublishData: true,
      canUpdateOwnMetadata: true,
    });

    const accessToken = await token.toJwt();

    return NextResponse.json({
      accessToken,
      url: livekitUrl,
      roomName,
      identity,
    });
  } catch (error) {
    console.error("Error creating LiveKit token:", error);
    return NextResponse.json(
      { error: "Failed to create access token" },
      { status: 500 }
    );
  }
}
