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

// Modern Glass Orb AI Avatar - Inspired by Reference Design
function RobotAvatar({
  isActive,
  isListening,
}: {
  isActive: boolean;
  isListening: boolean;
}) {
  const [blinkState, setBlinkState] = useState(false);
  const [pulseIntensity, setPulseIntensity] = useState(1);
  const [glowIntensity, setGlowIntensity] = useState(0.5);
  const [rotationAngle, setRotationAngle] = useState(0);

  // Simple Blinking System
  useEffect(() => {
    if (!isActive) return;

    const blinkInterval = setInterval(() => {
      const nextBlink = Math.random() * 4000 + 2000; // 2-6 seconds

      setTimeout(() => {
        setBlinkState(true);
        setTimeout(() => setBlinkState(false), 200);
      }, nextBlink);
    }, 100);

    return () => clearInterval(blinkInterval);
  }, [isActive]);

  // Pulse and Glow Animation
  useEffect(() => {
    if (!isActive) return;

    const pulseInterval = setInterval(() => {
      const time = Date.now();
      setPulseIntensity(Math.sin(time * 0.002) * 0.1 + 1);
      setGlowIntensity(Math.sin(time * 0.003) * 0.3 + 0.7);
      setRotationAngle(time * 0.00005); // Very slow rotation for shimmer effect
    }, 50);

    return () => clearInterval(pulseInterval);
  }, [isActive]);

  // Enhanced listening state animation
  useEffect(() => {
    if (isListening) {
      setPulseIntensity(1.15);
      setGlowIntensity(1.2);
    }
  }, [isListening]);

  return (
    <div className="relative w-40 h-40 mx-auto mb-8">
      {/* Glass Orb Container */}
      <div
        className="relative w-full h-full transition-all duration-500"
        style={{
          transform: `scale(${pulseIntensity}) rotate(${rotationAngle}deg)`,
        }}
      >
        {/* Ambient Shadow */}
        <div
          className="absolute inset-2 rounded-full blur-2xl transition-all duration-500"
          style={{
            background: isActive
              ? "radial-gradient(circle, rgba(34,229,140,0.4) 0%, rgba(34,229,140,0.2) 40%, transparent 70%)"
              : "radial-gradient(circle, rgba(22,58,51,0.3) 0%, rgba(22,58,51,0.1) 40%, transparent 70%)",
            opacity: glowIntensity * 0.6,
          }}
        />

        {/* Main Glass Orb */}
        <div
          className="absolute inset-0 rounded-full transition-all duration-500 overflow-hidden"
          style={{
            background: isActive
              ? `
                  radial-gradient(circle at 30% 30%, rgba(255,255,255,0.8) 0%, rgba(255,255,255,0.3) 20%, transparent 50%),
                  linear-gradient(135deg, 
                    rgba(34,229,140,0.9) 0%, 
                    rgba(26,203,121,0.8) 25%, 
                    rgba(0,229,193,0.7) 50%, 
                    rgba(22,180,100,0.8) 75%, 
                    rgba(18,150,88,0.9) 100%
                  ),
                  radial-gradient(circle at 70% 70%, rgba(0,0,0,0.3) 0%, transparent 60%)
                `
              : `
                  radial-gradient(circle at 30% 30%, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0.1) 20%, transparent 50%),
                  linear-gradient(135deg, 
                    rgba(22,58,51,0.6) 0%, 
                    rgba(16,45,38,0.7) 50%, 
                    rgba(12,35,30,0.8) 100%
                  )
                `,
            boxShadow: isActive
              ? `
                  inset 0 0 30px rgba(255,255,255,0.2),
                  inset 0 -20px 30px rgba(0,0,0,0.2),
                  0 0 50px rgba(34,229,140,${glowIntensity * 0.5}),
                  0 0 100px rgba(34,229,140,${glowIntensity * 0.3})
                `
              : `
                  inset 0 0 20px rgba(255,255,255,0.1),
                  inset 0 -15px 20px rgba(0,0,0,0.3)
                `,
          }}
        >
          {/* Glass Reflection Highlights */}
          <div
            className="absolute inset-0 rounded-full"
            style={{
              background: `
                radial-gradient(ellipse 40% 60% at 25% 25%, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.4) 40%, transparent 70%),
                radial-gradient(ellipse 20% 30% at 75% 25%, rgba(255,255,255,0.6) 0%, transparent 50%),
                linear-gradient(45deg, transparent 0%, rgba(255,255,255,0.1) 20%, transparent 40%)
              `,
              opacity: isActive ? 1 : 0.6,
            }}
          />

          {/* Simple Pill-shaped Eyes */}
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 flex gap-4">
            {["left", "right"].map((side) => (
              <div key={side} className="relative">
                <div
                  className="w-6 h-3 rounded-full transition-all duration-200"
                  style={{
                    background: isActive
                      ? "rgba(255,255,255,0.95)"
                      : "rgba(255,255,255,0.7)",
                    boxShadow: isActive
                      ? "0 0 10px rgba(255,255,255,0.5), inset 0 1px 2px rgba(0,0,0,0.1)"
                      : "inset 0 1px 2px rgba(0,0,0,0.2)",
                    transform: `scaleY(${blinkState ? 0.1 : 1})`,
                  }}
                >
                  {/* Inner glow */}
                  <div
                    className="absolute inset-0 rounded-full"
                    style={{
                      background:
                        "radial-gradient(ellipse 60% 40% at 50% 30%, rgba(255,255,255,0.8) 0%, transparent 70%)",
                    }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Listening pulse effect */}
          {isListening && (
            <div className="absolute inset-0 rounded-full">
              {[...Array(3)].map((_, i) => (
                <div
                  key={i}
                  className="absolute inset-0 rounded-full border-2 animate-ping"
                  style={{
                    borderColor: "rgba(255,255,255,0.4)",
                    opacity: 0.6 - i * 0.2,
                    animationDelay: `${i * 0.3}s`,
                    animationDuration: "2s",
                  }}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Clean Ambient Glow */}
      {isActive && (
        <div
          className="absolute -inset-6 rounded-full animate-pulse transition-all duration-1000"
          style={{
            background: `radial-gradient(circle, rgba(34,229,140,${
              glowIntensity * 0.3
            }) 0%, rgba(34,229,140,${
              glowIntensity * 0.1
            }) 50%, transparent 80%)`,
            filter: "blur(15px)",
            opacity: 0.8,
          }}
        />
      )}
    </div>
  );
}

function AudioVisualizer({ isActive }: { isActive: boolean }) {
  // Add CSS animations for 3D effects
  useEffect(() => {
    const style = document.createElement("style");
    style.textContent = `
      @keyframes scan {
        0% { transform: translateY(-100%); }
        100% { transform: translateY(100%); }
      }
      .perspective-1000 {
        perspective: 1000px;
      }
      .transform-gpu {
        transform: translateZ(0);
      }
    `;
    document.head.appendChild(style);

    return () => {
      document.head.removeChild(style);
    };
  }, []);

  return (
    <div className="flex items-end justify-center space-x-2 h-20 w-40 mx-auto">
      {[...Array(9)].map((_, i) => (
        <div
          key={i}
          className={`w-1.5 bg-gradient-to-t from-[#22E58C] via-[#1ACB79] to-[#00E5C1] rounded-full transition-all duration-500 ease-in-out ${
            isActive
              ? "animate-pulse shadow-[0_0_8px_rgba(34,229,140,0.6)]"
              : ""
          }`}
          style={{
            height: isActive
              ? `${Math.sin(Date.now() * 0.005 + i) * 25 + 35}px`
              : `${8 + i * 2}px`,
            animationDelay: `${i * 0.12}s`,
            opacity: isActive ? 0.9 : 0.3,
          }}
        />
      ))}
    </div>
  );
}

interface ConnectionDetails {
  accessToken: string;
  url: string;
  roomName: string;
  identity: string;
}

// Professional Voice Assistant Interface - Hero Theme
function VoiceAssistantUI({ embedded = false }: { embedded?: boolean }) {
  const connectionState = useConnectionState();
  const { state: agentState } = useVoiceAssistant();
  const [audioInitialized, setAudioInitialized] = useState(false);
  const [sessionTime, setSessionTime] = useState(0);

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

  // Session timer
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (connectionState === ConnectionState.Connected) {
      interval = setInterval(() => {
        setSessionTime((prev) => prev + 1);
      }, 1000);
    } else {
      setSessionTime(0);
    }
    return () => clearInterval(interval);
  }, [connectionState]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs
      .toString()
      .padStart(2, "0")}`;
  };

  const getStatusInfo = () => {
    switch (connectionState) {
      case ConnectionState.Disconnected:
        return {
          text: "Disconnected",
          color: "text-red-400",
          bgColor: "bg-red-400/20",
          borderColor: "border-red-400/30",
        };
      case ConnectionState.Connecting:
        return {
          text: "Connecting...",
          color: "text-amber-400",
          bgColor: "bg-amber-400/20",
          borderColor: "border-amber-400/30",
        };
      case ConnectionState.Connected:
        return {
          text: "Connected",
          color: "text-[#22E58C]",
          bgColor: "bg-[#22E58C]/20",
          borderColor: "border-[#22E58C]/30",
        };
      case ConnectionState.Reconnecting:
        return {
          text: "Reconnecting...",
          color: "text-amber-400",
          bgColor: "bg-amber-400/20",
          borderColor: "border-amber-400/30",
        };
      default:
        return {
          text: "Unknown",
          color: "text-[#A4B9B0]",
          bgColor: "bg-[#A4B9B0]/20",
          borderColor: "border-[#A4B9B0]/30",
        };
    }
  };

  const statusInfo = getStatusInfo();

  return (
    <div
      className={
        embedded
          ? "absolute inset-0 overflow-hidden"
          : "fixed inset-0 overflow-hidden"
      }
    >
      {/* Professional Header Bar */}
      <div className="absolute top-0 left-0 right-0 z-30 bg-[#0A0F0D]/80 backdrop-blur-xl border-b border-[#163A33]/30">
        <div className="flex items-center justify-between px-6 py-4">
          {/* Session Info */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-[#22E58C] rounded-full animate-pulse"></div>
              <span className="text-[#E7F7F0] text-sm font-medium">
                VOICEAI Session
              </span>
            </div>
            {connectionState === ConnectionState.Connected && (
              <div className="text-[#A4B9B0] text-sm">
                {formatTime(sessionTime)}
              </div>
            )}
          </div>

          {/* Status Indicator */}
          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${statusInfo.bgColor} ${statusInfo.borderColor} border backdrop-blur-sm`}
          >
            <div
              className={`w-2 h-2 rounded-full ${statusInfo.color.replace(
                "text-",
                "bg-"
              )} ${
                connectionState === ConnectionState.Connecting
                  ? "animate-pulse"
                  : ""
              }`}
            ></div>
            <span className={`text-xs font-medium ${statusInfo.color}`}>
              {statusInfo.text}
            </span>
          </div>
        </div>
      </div>

      {/* Main Interface */}
      <div className="absolute inset-0 pt-16 flex items-center justify-center">
        <div className="w-full max-w-2xl px-8">
          {connectionState === ConnectionState.Connected ? (
            <div className="text-center space-y-12">
              {/* AI Avatar Section */}
              <div className="relative">
                <div className="flex justify-center mb-8">
                  <div className="relative">
                    <RobotAvatar
                      isActive={connectionState === ConnectionState.Connected}
                      isListening={
                        connectionState === ConnectionState.Connected
                      }
                    />

                    {/* Floating Status Cards */}
                    <div className="absolute -left-20 top-8 hidden lg:block">
                      <div className="bg-[#163A33]/40 backdrop-blur-sm border border-[#163A33]/60 rounded-xl p-3 text-left">
                        <div className="text-[#22E58C] text-xs font-medium mb-1">
                          AI Status
                        </div>
                        <div className="text-[#E7F7F0] text-sm">
                          Active & Listening
                        </div>
                      </div>
                    </div>

                    <div className="absolute -right-20 top-16 hidden lg:block">
                      <div className="bg-[#163A33]/40 backdrop-blur-sm border border-[#163A33]/60 rounded-xl p-3 text-left">
                        <div className="text-[#22E58C] text-xs font-medium mb-1">
                          Audio Quality
                        </div>
                        <div className="text-[#E7F7F0] text-sm">
                          HD • Low Latency
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Audio Visualizer */}
                <div className="flex justify-center mb-8">
                  <AudioVisualizer
                    isActive={connectionState === ConnectionState.Connected}
                  />
                </div>

                {/* Main Status */}
                <div className="space-y-4">
                  <h1 className="text-3xl font-bold text-transparent bg-gradient-to-r from-[#22E58C] via-[#00E5C1] to-[#1ACB79] bg-clip-text">
                    AI Assistant Ready
                  </h1>
                  <p className="text-[#A4B9B0] text-lg max-w-md mx-auto leading-relaxed">
                    I'm listening and ready to help. Speak naturally - I can
                    understand and respond to your questions.
                  </p>
                </div>
              </div>

              {/* Interactive Features */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-3xl mx-auto">
                {/* Voice Commands */}
                <div className="bg-[#163A33]/20 backdrop-blur-sm border border-[#163A33]/40 rounded-xl p-4 hover:bg-[#163A33]/30 transition-all duration-300">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-8 h-8 bg-[#22E58C]/20 rounded-lg flex items-center justify-center">
                      <svg
                        className="w-4 h-4 text-[#22E58C]"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                        />
                      </svg>
                    </div>
                    <h3 className="text-[#E7F7F0] font-medium">
                      Voice Commands
                    </h3>
                  </div>
                  <p className="text-[#A4B9B0] text-sm">
                    Natural speech recognition with instant responses
                  </p>
                </div>

                {/* Smart Assistance */}
                <div className="bg-[#163A33]/20 backdrop-blur-sm border border-[#163A33]/40 rounded-xl p-4 hover:bg-[#163A33]/30 transition-all duration-300">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-8 h-8 bg-[#22E58C]/20 rounded-lg flex items-center justify-center">
                      <svg
                        className="w-4 h-4 text-[#22E58C]"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                        />
                      </svg>
                    </div>
                    <h3 className="text-[#E7F7F0] font-medium">Smart AI</h3>
                  </div>
                  <p className="text-[#A4B9B0] text-sm">
                    Intelligent responses powered by advanced AI
                  </p>
                </div>

                {/* Real-time Processing */}
                <div className="bg-[#163A33]/20 backdrop-blur-sm border border-[#163A33]/40 rounded-xl p-4 hover:bg-[#163A33]/30 transition-all duration-300">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-8 h-8 bg-[#22E58C]/20 rounded-lg flex items-center justify-center">
                      <svg
                        className="w-4 h-4 text-[#22E58C]"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M13 10V3L4 14h7v7l9-11h-7z"
                        />
                      </svg>
                    </div>
                    <h3 className="text-[#E7F7F0] font-medium">Real-time</h3>
                  </div>
                  <p className="text-[#A4B9B0] text-sm">
                    Ultra-low latency for natural conversations
                  </p>
                </div>
              </div>

              {/* Audio Controls */}
              {!audioInitialized && (
                <div className="flex justify-center">
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
                        }
                      } catch (error) {
                        console.error("Failed to activate audio:", error);
                      }
                    }}
                    className="px-8 py-3 bg-[#22E58C] hover:bg-[#1ACB79] text-[#072517] font-semibold rounded-xl transition-all duration-300 shadow-[0_8px_30px_rgba(34,229,140,0.25)] hover:shadow-[0_12px_40px_rgba(34,229,140,0.35)] hover:scale-[1.02] flex items-center gap-2"
                  >
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
                      />
                    </svg>
                    Enable Audio
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center space-y-12">
              {/* Professional Loading State */}
              <div className="relative">
                <div className="flex justify-center mb-8">
                  <div className="relative">
                    {/* Animated Loading Ring */}
                    <div className="w-32 h-32 rounded-full border-2 border-[#163A33]/40 relative">
                      <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-[#22E58C] animate-spin"></div>
                      <div className="absolute inset-2 rounded-full border border-[#163A33]/20 bg-[#0C1412]/60 backdrop-blur-sm flex items-center justify-center">
                        <svg
                          className="w-8 h-8 text-[#22E58C] animate-pulse"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                          />
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h1 className="text-2xl font-bold text-[#E7F7F0]">
                    Initializing AI Assistant
                  </h1>
                  <p className="text-[#A4B9B0] text-lg max-w-md mx-auto">
                    Establishing secure connection and preparing voice
                    recognition...
                  </p>
                </div>
              </div>

              {/* Loading Steps */}
              <div className="max-w-md mx-auto space-y-3">
                <div className="flex items-center gap-3 p-3 bg-[#163A33]/20 rounded-lg border border-[#163A33]/40">
                  <div className="w-2 h-2 bg-[#22E58C] rounded-full animate-pulse"></div>
                  <span className="text-[#E7F7F0] text-sm">
                    Connecting to server...
                  </span>
                </div>
                <div className="flex items-center gap-3 p-3 bg-[#163A33]/10 rounded-lg border border-[#163A33]/20">
                  <div className="w-2 h-2 bg-[#A4B9B0]/40 rounded-full"></div>
                  <span className="text-[#A4B9B0] text-sm">
                    Initializing AI model...
                  </span>
                </div>
                <div className="flex items-center gap-3 p-3 bg-[#163A33]/10 rounded-lg border border-[#163A33]/20">
                  <div className="w-2 h-2 bg-[#A4B9B0]/40 rounded-full"></div>
                  <span className="text-[#A4B9B0] text-sm">
                    Setting up audio processing...
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* CRITICAL: Audio Rendering */}
      <RoomAudioRenderer />
    </div>
  );
}

export default function VoiceChat({
  embedded = false,
  onBack,
}: {
  embedded?: boolean;
  onBack?: () => void;
}) {
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
    <div
      className={
        embedded
          ? "relative h-full w-full overflow-hidden"
          : "fixed inset-0 bg-slate-950 overflow-hidden"
      }
    >
      {/* Modern Hero-themed background */}
      <div
        className={
          embedded
            ? "absolute inset-0 bg-gradient-to-b from-[#0A0F0D]/90 via-[#0C1412]/90 to-[#0A0F0D]/90"
            : "absolute inset-0 bg-gradient-to-b from-[#0A0F0D] via-[#0C1412] to-[#0A0F0D]"
        }
      ></div>

      {/* Hero-style background effects */}
      <div className="absolute inset-0 pointer-events-none">
        <div
          className="absolute inset-0"
          style={{
            background: `
              radial-gradient(50% 40% at 50% 35%, rgba(0,229,193,0.04) 0%, rgba(0,0,0,0) 70%),
              radial-gradient(60% 30% at 50% 100%, rgba(34,229,140,0.08) 0%, rgba(0,0,0,0) 80%),
              radial-gradient(100% 80% at 50% 50%, rgba(0,0,0,0) 60%, rgba(0,0,0,0.7) 100%)
            `,
          }}
        />
      </div>

      <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-[40rem] h-[40rem] bg-[#22E58C]/5 rounded-full blur-3xl"></div>

      {/* Back button - only show when onBack is provided */}
      {onBack && (
        <button
          onClick={onBack}
          className="absolute top-6 left-6 z-50 flex items-center gap-2 px-4 py-2 bg-[#163A33]/40 hover:bg-[#22E58C]/20 border border-[#163A33]/60 hover:border-[#22E58C]/40 rounded-lg text-[#A4B9B0] hover:text-[#22E58C] transition-all duration-300 backdrop-blur-sm shadow-[0_4px_15px_rgba(0,0,0,0.3)]"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
          Back to Home
        </button>
      )}

      <div
        className={
          embedded
            ? "absolute inset-0 flex items-center justify-center"
            : "absolute inset-0 flex items-center justify-center"
        }
      >
        {!connectionDetails ? (
          <div className="w-full max-w-2xl text-center space-y-12 px-8">
            {/* Professional Header */}
            <div className="space-y-4">
              <div className="flex justify-center">
                <div className="relative gap-6">
                  <RobotAvatar isActive={false} isListening={false} />

                  {/* Floating Welcome Cards */}
                  <div className="absolute -left-42 top-12 hidden xl:block gap-6">
                    <div className="bg-[#163A33]/40 backdrop-blur-sm border border-[#163A33]/60 rounded-xl p-4 text-left transform rotate-[-2deg]">
                      <div className="text-[#22E58C] text-xs font-medium mb-1">
                        ✨ AI-Powered
                      </div>
                      <div className="text-[#E7F7F0] text-sm">
                        Natural Conversations
                      </div>
                    </div>
                  </div>

                  <div className="absolute -right-42 top-20 hidden xl:block gap-6">
                    <div className="bg-[#163A33]/40 backdrop-blur-sm border border-[#163A33]/60 rounded-xl p-4 text-left transform rotate-[2deg]">
                      <div className="text-[#22E58C] text-xs font-medium mb-1">
                        🔒 Secure
                      </div>
                      <div className="text-[#E7F7F0] text-sm">
                        End-to-End Encrypted
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h1 className="text-4xl font-bold text-transparent bg-gradient-to-r from-[#22E58C] via-[#00E5C1] to-[#1ACB79] bg-clip-text tracking-tight">
                  VOICEAI
                </h1>
                <p className="text-[#A4B9B0] text-xl max-w-lg mx-auto leading-relaxed">
                  Your intelligent AI voice assistant powered by advanced
                  language models
                </p>
              </div>
            </div>

            {/* Professional Connection Form */}
            <div className="max-w-md mx-auto space-y-8">
              <div className="bg-[#163A33]/20 backdrop-blur-sm border border-[#163A33]/40 rounded-2xl p-8 space-y-6">
                <div className="text-center space-y-2">
                  <h2 className="text-[#E7F7F0] text-lg font-semibold">
                    Start Your Session
                  </h2>
                  <p className="text-[#A4B9B0] text-sm">
                    Enter your name to begin the conversation
                  </p>
                </div>

                <div className="space-y-4">
                  <div className="relative">
                    <input
                      type="text"
                      value={participantName}
                      onChange={(e) => setParticipantName(e.target.value)}
                      onKeyPress={(e) => e.key === "Enter" && connectToAgent()}
                      placeholder="Your name..."
                      className="w-full px-4 py-4 bg-[#0C1412]/60 border border-[#163A33]/60 rounded-xl text-[#E7F7F0] placeholder-[#A4B9B0] focus:outline-none focus:ring-2 focus:ring-[#22E58C]/50 focus:border-[#22E58C]/40 transition-all duration-300 backdrop-blur-sm text-center font-medium"
                      disabled={isConnecting}
                    />
                    <div className="absolute inset-x-0 -bottom-1 h-px bg-gradient-to-r from-transparent via-[#22E58C]/30 to-transparent"></div>
                  </div>

                  {error && (
                    <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm text-center backdrop-blur-sm">
                      <div className="flex items-center justify-center gap-2">
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                        {error}
                      </div>
                    </div>
                  )}

                  <button
                    onClick={connectToAgent}
                    disabled={isConnecting || !participantName.trim()}
                    className="w-full px-8 py-4 bg-[#22E58C] hover:bg-[#1ACB79] disabled:bg-[#163A33]/40 disabled:text-[#A4B9B0] text-[#072517] font-bold rounded-xl transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-[#22E58C]/50 shadow-[0_8px_30px_rgba(34,229,140,0.25)] hover:shadow-[0_12px_40px_rgba(34,229,140,0.35)] hover:scale-[1.02] flex items-center justify-center gap-3 text-lg"
                  >
                    {isConnecting ? (
                      <>
                        <div className="w-5 h-5 border-2 border-[#072517] border-t-transparent rounded-full animate-spin"></div>
                        Connecting...
                      </>
                    ) : (
                      <>
                        <svg
                          className="w-5 h-5"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                          />
                        </svg>
                        START VOICE SESSION
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Professional Footer */}
            <div className="text-center space-y-4">
              <p className="text-[#A4B9B0]/70 text-sm max-w-md mx-auto">
                Experience natural conversations with our advanced AI assistant.
                Powered by cutting-edge language models.
              </p>
              <div className="flex items-center justify-center gap-4 text-xs text-[#A4B9B0]/50">
                <span>🔒 End-to-End Encrypted</span>
                <span>•</span>
                <span>⚡ Real-time Processing</span>
                <span>•</span>
                <span>🎯 Context Aware</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="w-full">
            {/* Professional Disconnect Button */}
            <div className="absolute top-6 right-6 z-20">
              <button
                onClick={disconnectFromAgent}
                className="flex items-center gap-2 px-4 py-2 bg-[#163A33]/40 hover:bg-red-500/20 border border-[#163A33]/60 hover:border-red-500/40 rounded-lg text-[#A4B9B0] hover:text-red-400 text-sm font-medium transition-all duration-300 backdrop-blur-sm shadow-[0_4px_15px_rgba(0,0,0,0.3)]"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                  />
                </svg>
                END SESSION
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
              className={
                embedded ? "livekit-room relative h-full" : "livekit-room"
              }
            >
              <VoiceAssistantUI embedded={embedded} />
            </LiveKitRoom>

            {/* Debug Info */}
            {process.env.NODE_ENV === "development" && (
              <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 z-20">
                <div className="p-3 bg-white/5 border border-white/10 rounded-lg text-xs text-slate-400">
                  <div className="flex flex-wrap gap-4">
                    <span>Room: {connectionDetails.roomName}</span>
                    <span>Identity: {connectionDetails.identity}</span>
                    <span>
                      Server: {connectionDetails.url.replace(/^wss?:\/\//, "")}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}