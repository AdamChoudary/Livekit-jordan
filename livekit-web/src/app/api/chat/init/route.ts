import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    // Call your Python agent's init endpoint
    const response = await fetch("http://localhost:8000/api/chat/init", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error("Failed to initialize chat");
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Chat init error:", error);
    return NextResponse.json(
      { error: "Failed to initialize chat" },
      { status: 500 }
    );
  }
}
