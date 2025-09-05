"use client";

import {
  LiveKitRoom,
  useConnectionState,
  useVoiceAssistant,
  RoomAudioRenderer,
} from "@livekit/components-react";
import { ConnectionState } from "livekit-client";
import "@livekit/components-styles/prefabs";
import { useState, useCallback, useEffect } from "react";

interface ConnectionDetails {
  accessToken: string;
  url: string;
  roomName: string;
  identity: string;
}

// Inner component that works within the LiveKit Room context
function VoiceAssistantComponent() {
  const connectionState = useConnectionState();
  const { state: agentState } = useVoiceAssistant();
  const [audioInitialized, setAudioInitialized] = useState(false);

  // Initialize audio context on first user interaction
  useEffect(() => {
    const initializeAudio = async () => {
      try {
        // Resume audio context if it's suspended (browser audio policy)
        if (typeof window !== "undefined" && "webkitAudioContext" in window) {
          const AudioContext =
            window.AudioContext || (window as any).webkitAudioContext;
          const audioContext = new AudioContext();
          if (audioContext.state === "suspended") {
            await audioContext.resume();
          }
          setAudioInitialized(true);
          console.log("✅ Audio context initialized");
        }
      } catch (error) {
        console.error("❌ Failed to initialize audio context:", error);
      }
    };

    if (connectionState === ConnectionState.Connected && !audioInitialized) {
      initializeAudio();
    }
  }, [connectionState, audioInitialized]);

  const getStatusText = () => {
    switch (connectionState) {
      case ConnectionState.Disconnected:
        return "Disconnected";
      case ConnectionState.Connecting:
        return "Connecting...";
      case ConnectionState.Connected:
        return "Connected";
      case ConnectionState.Reconnecting:
        return "Reconnecting...";
      default:
        return "Unknown Status";
    }
  };

  return (
    <div>
      {/* Status Display */}
      <div className="flex justify-center items-center mb-6">
        <div className="flex items-center space-x-2">
          <div
            className={`w-4 h-4 rounded-full ${
              connectionState === ConnectionState.Connected
                ? "bg-green-500"
                : connectionState === ConnectionState.Connecting
                ? "bg-orange-500"
                : "bg-gray-400"
            }`}
          ></div>
          <span className="text-sm font-medium">{getStatusText()}</span>
        </div>
      </div>

      {/* Agent Instructions */}
      <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <h3 className="font-semibold text-blue-900 mb-2">How to use:</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Speak naturally - the agent will listen and respond</li>
          <li>• You can interrupt the agent at any time</li>
          <li>• Ask about products, orders, customer support, etc.</li>
          <li>
            • The agent has access to your customer information and order
            history
          </li>
        </ul>
      </div>

      {/* Voice Chat Status */}
      <div className="text-center p-6 bg-green-50 rounded-lg border border-green-200">
        {connectionState === ConnectionState.Connected ? (
          <div>
            <div className="text-2xl mb-2">🎤</div>
            <h3 className="text-lg font-semibold text-green-900 mb-2">
              Voice Chat Active!
            </h3>
            <p className="text-green-800">
              You're connected to the AI customer support agent. Start speaking!
            </p>

            {/* Agent Status */}
            <div className="mt-4 text-sm text-green-700">
              {agentState ? (
                <div>✅ Agent is {agentState} and ready!</div>
              ) : (
                <div>⏳ Waiting for agent to join...</div>
              )}
              {audioInitialized ? (
                <div className="text-xs text-gray-600 mt-1">
                  🔊 Audio context active
                </div>
              ) : (
                <div className="mt-2">
                  <div className="text-xs text-orange-600 mb-2">
                    🔇 Audio context suspended
                  </div>
                  <button
                    onClick={async () => {
                      try {
                        if (typeof window !== "undefined") {
                          const AudioContext =
                            window.AudioContext ||
                            (window as any).webkitAudioContext;
                          const audioContext = new AudioContext();
                          await audioContext.resume();
                          setAudioInitialized(true);
                          console.log("✅ Audio manually activated");
                        }
                      } catch (error) {
                        console.error("❌ Failed to activate audio:", error);
                      }
                    }}
                    className="px-3 py-1 bg-orange-500 text-white text-xs rounded hover:bg-orange-600 transition-colors"
                  >
                    🔊 Enable Audio
                  </button>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div>
            <div className="text-2xl mb-2">⏳</div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Connecting...
            </h3>
            <p className="text-gray-700">
              Setting up your voice connection with the agent...
            </p>
          </div>
        )}
      </div>

      {/* CRITICAL: Audio Rendering - This makes agent voice audible! */}
      <RoomAudioRenderer />
    </div>
  );
}

export default function VoiceChat() {
  const [connectionDetails, setConnectionDetails] =
    useState<ConnectionDetails | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [participantName, setParticipantName] = useState("");
  const [error, setError] = useState<string | null>(null);

  const connectToAgent = useCallback(async () => {
    if (!participantName.trim()) {
      setError("Please enter your name");
      return;
    }

    setIsConnecting(true);
    setError(null);

    try {
      const response = await fetch("/api/livekit", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          participantName: participantName.trim(),
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to get connection details");
      }

      const details: ConnectionDetails = await response.json();
      setConnectionDetails(details);
    } catch (err) {
      console.error("Connection error:", err);
      setError(err instanceof Error ? err.message : "Connection failed");
    } finally {
      setIsConnecting(false);
    }
  }, [participantName]);

  const disconnectFromAgent = useCallback(() => {
    setConnectionDetails(null);
    setParticipantName("");
  }, []);

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">
          Customer Support Voice Agent
        </h1>
        <p className="text-gray-600">
          Connect with our AI-powered customer support agent via voice chat
        </p>
      </div>

      {/* Connection Card */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        {!connectionDetails ? (
          <div className="text-center">
            <div className="mb-6">
              <label
                htmlFor="name"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Your Name
              </label>
              <input
                id="name"
                type="text"
                value={participantName}
                onChange={(e) => setParticipantName(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && connectToAgent()}
                placeholder="Enter your name..."
                className="w-full max-w-md px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isConnecting}
              />
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-100 border border-red-300 text-red-700 rounded-lg">
                {error}
              </div>
            )}

            <button
              onClick={connectToAgent}
              disabled={isConnecting || !participantName.trim()}
              className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isConnecting ? (
                <div className="flex items-center">
                  <svg
                    className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                  Connecting...
                </div>
              ) : (
                "🎤 Start Voice Chat"
              )}
            </button>
          </div>
        ) : (
          <div>
            {/* Disconnect Button */}
            <div className="flex justify-end mb-4">
              <button
                onClick={disconnectFromAgent}
                className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 transition-colors"
              >
                Disconnect
              </button>
            </div>

            {/* LiveKit Room Component */}
            <LiveKitRoom
              token={connectionDetails.accessToken}
              serverUrl={connectionDetails.url}
              connect={true}
              audio={true}
              video={false}
              onError={(error) => {
                console.error("LiveKit error:", error);
                setError(`Connection error: ${error.message}`);
              }}
              onConnected={() => {
                console.log("✅ Connected to LiveKit room");
              }}
              onDisconnected={() => {
                console.log("❌ Disconnected from LiveKit room");
              }}
              className="livekit-room"
            >
              <VoiceAssistantComponent />
            </LiveKitRoom>

            {/* Connection Info (Debug) */}
            {process.env.NODE_ENV === "development" && (
              <div className="mt-4 p-3 bg-gray-100 rounded text-xs text-gray-600">
                <p>
                  <strong>Room:</strong> {connectionDetails.roomName}
                </p>
                <p>
                  <strong>Identity:</strong> {connectionDetails.identity}
                </p>
                <p>
                  <strong>Server:</strong> {connectionDetails.url}
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Features */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-2xl mb-2">🛒</div>
          <h3 className="font-semibold mb-1">Order Management</h3>
          <p className="text-sm text-gray-600">
            Place, track, and cancel orders
          </p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-2xl mb-2">📦</div>
          <h3 className="font-semibold mb-1">Product Search</h3>
          <p className="text-sm text-gray-600">
            Find products across categories
          </p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-2xl mb-2">👤</div>
          <h3 className="font-semibold mb-1">Customer Service</h3>
          <p className="text-sm text-gray-600">Account info and support</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-2xl mb-2">💬</div>
          <h3 className="font-semibold mb-1">Natural Voice</h3>
          <p className="text-sm text-gray-600">Human-like conversation</p>
        </div>
      </div>
    </div>
  );
}
