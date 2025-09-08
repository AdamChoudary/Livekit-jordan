"use client";

import { useState, useCallback, useEffect } from "react";
import { useLocalParticipant } from "@livekit/components-react";

interface Voice {
  id: string;
  name: string;
  gender: "male" | "female";
  description: string;
  provider: string;
  model: string;
  accent?: string;
  personality?: string;
  previewText?: string;
}

const AVAILABLE_VOICES: Voice[] = [
  {
    id: "luna",
    name: "Luna",
    gender: "female",
    description: "Warm & Professional",
    provider: "deepgram",
    model: "aura-luna-en",
    accent: "American",
    personality: "Empathetic business consultant with warm, trustworthy tone",
    previewText:
      "Hello! I'm Luna, your professional AI assistant. How can I help you today?",
  },
  {
    id: "stella",
    name: "Stella",
    gender: "female",
    description: "Energetic & Upbeat",
    provider: "deepgram",
    model: "aura-stella-en",
    accent: "American",
    personality: "Enthusiastic team leader with vibrant, motivating energy",
    previewText:
      "Hi there! I'm Stella, and I'm excited to assist you with lots of positive energy!",
  },
  {
    id: "athena",
    name: "Athena",
    gender: "female",
    description: "Professional & Authoritative",
    provider: "deepgram",
    model: "aura-athena-en",
    accent: "American",
    personality: "Executive assistant with clear, authoritative delivery",
    previewText:
      "Good day. I'm Athena, your professional business assistant. How may I assist you?",
  },
  {
    id: "orion",
    name: "Orion",
    gender: "male",
    description: "Deep & Confident",
    provider: "deepgram",
    model: "aura-orion-en",
    accent: "American",
    personality: "Senior advisor with commanding, reassuring presence",
    previewText:
      "Hello. I'm Orion, your confident AI advisor. I'm here to help with any questions.",
  },
  {
    id: "arcas",
    name: "Arcas",
    gender: "male",
    description: "Friendly & Casual",
    provider: "deepgram",
    model: "aura-arcas-en",
    accent: "American",
    personality: "Approachable colleague with relaxed, conversational style",
    previewText:
      "Hey! I'm Arcas, your friendly AI assistant. What can I do for you today?",
  },
];

interface VoiceSelectorProps {
  currentVoice: string;
  onVoiceChange: (voiceId: string) => void;
  isConnected: boolean;
}

export default function VoiceSelector({
  currentVoice,
  onVoiceChange,
  isConnected,
}: VoiceSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isChanging, setIsChanging] = useState(false);
  const [localCurrentVoice, setLocalCurrentVoice] = useState(currentVoice);
  const [previewingVoice, setPreviewingVoice] = useState<string | null>(null);
  const { localParticipant } = useLocalParticipant();

  // Load saved voice preference on mount
  useEffect(() => {
    const savedVoice = localStorage.getItem("preferred_voice");
    if (savedVoice && AVAILABLE_VOICES.find((v) => v.id === savedVoice)) {
      setLocalCurrentVoice(savedVoice);
      onVoiceChange(savedVoice);
    }
  }, [onVoiceChange]);

  // Sync localCurrentVoice with currentVoice prop when it changes
  useEffect(() => {
    if (currentVoice && currentVoice !== localCurrentVoice) {
      setLocalCurrentVoice(currentVoice);
    }
  }, [currentVoice, localCurrentVoice]);

  // Listen for data messages from backend
  useEffect(() => {
    if (!localParticipant) return;

    const handleDataReceived = (payload: Uint8Array) => {
      try {
        const message = JSON.parse(new TextDecoder().decode(payload));
        console.log("📨 VoiceSelector received data:", message);

        if (message.type === "voice_change_response") {
          console.log("🎙️ Voice change response:", message);
          setIsChanging(false);

          if (message.success) {
            console.log(
              "✅ Voice change successful, updating to:",
              message.currentVoice
            );
            setLocalCurrentVoice(message.currentVoice);
            onVoiceChange(message.currentVoice);
            localStorage.setItem("preferred_voice", message.currentVoice);
          } else {
            console.log("❌ Voice change failed:", message.message);
          }
        } else if (message.type === "test_message") {
          console.log(
            "🧪 Test message received from backend:",
            message.message
          );
        }
      } catch (error) {
        console.error("❌ Error parsing data message:", error);
      }
    };

    // Use the correct event listener for LiveKit
    localParticipant.on("dataReceived", handleDataReceived);

    return () => {
      localParticipant.off("dataReceived", handleDataReceived);
    };
  }, [localParticipant, onVoiceChange]);

  const handleVoiceChange = useCallback(
    async (voiceId: string) => {
      if (!isConnected || isChanging || voiceId === localCurrentVoice) return;

      setIsChanging(true);
      setIsOpen(false);

      try {
        console.log("🚀 Sending voice change request:", voiceId);

        // Send voice change request via data channel
        if (localParticipant) {
          const message = {
            type: "voice_change",
            voiceId: voiceId,
          };

          console.log("📤 Publishing data message:", message);
          await localParticipant.publishData(
            new TextEncoder().encode(JSON.stringify(message)),
            { reliable: true }
          );

          console.log("✅ Voice change request sent successfully");

          // Set timeout to reset changing state if no response
          setTimeout(() => {
            setIsChanging(false);
          }, 5000);
        }
      } catch (error) {
        console.error("Error changing voice:", error);
        setIsChanging(false);
      }
    },
    [isConnected, isChanging, localCurrentVoice, localParticipant]
  );

  const handleVoicePreview = useCallback(
    async (voiceId: string) => {
      if (!isConnected || previewingVoice) return;

      setPreviewingVoice(voiceId);

      try {
        const voice = AVAILABLE_VOICES.find((v) => v.id === voiceId);
        if (!voice || !localParticipant) return;

        console.log("Requesting voice preview:", voiceId);

        // Send voice preview request via data channel
        const message = {
          type: "voice_preview",
          voiceId: voiceId,
          previewText: voice.previewText || `Hello, I'm ${voice.name}.`,
        };

        await localParticipant.publishData(
          new TextEncoder().encode(JSON.stringify(message)),
          { reliable: true }
        );

        console.log("Voice preview request sent successfully");

        // Reset preview state after timeout
        setTimeout(() => {
          setPreviewingVoice(null);
        }, 4000);
      } catch (error) {
        console.error("Error requesting voice preview:", error);
        setPreviewingVoice(null);
      }
    },
    [isConnected, previewingVoice, localParticipant]
  );

  const currentVoiceData =
    AVAILABLE_VOICES.find((v) => v.id === localCurrentVoice) ||
    AVAILABLE_VOICES[0];

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      if (isOpen && !target.closest(".voice-selector")) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen]);

  return (
    <div className="relative voice-selector">
      {/* Modern Minimal Voice Selector */}
      <div className="bg-[#0C1412]/80 backdrop-blur-2xl border border-[#22E58C]/15 rounded-xl shadow-xl shadow-black/20 overflow-hidden">
        {/* Simplified Header */}
        <div className="px-5 py-3 border-b border-[#22E58C]/8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 rounded-full bg-[#22E58C] animate-pulse" />
              <span className="text-white font-medium text-sm">
                Voice Settings
              </span>
            </div>
            {isConnected ? (
              <div className="px-2 py-1 rounded-md bg-[#22E58C]/10 text-[#22E58C] text-xs font-medium">
                Online
              </div>
            ) : (
              <div className="px-2 py-1 rounded-md bg-red-500/10 text-red-400 text-xs font-medium">
                Offline
              </div>
            )}
          </div>
        </div>

        {/* Current Voice Display */}
        <div className="px-5 py-4">
          {/* Clean Current Voice Card */}
          <button
            onClick={() => setIsOpen(!isOpen)}
            disabled={!isConnected || isChanging}
            className={`
              w-full text-left p-4 rounded-lg border transition-all duration-300 group
              ${
                isConnected && !isChanging
                  ? "bg-[#22E58C]/5 border-[#22E58C]/20 hover:bg-[#22E58C]/10 hover:border-[#22E58C]/30"
                  : "bg-gray-800/20 border-gray-600/30 cursor-not-allowed opacity-60"
              }
            `}
          >
            <div className="flex items-center space-x-3">
              {/* Simple Voice Avatar */}
              <div className="relative flex-shrink-0">
                <div
                  className={`w-10 h-10 rounded-lg border flex items-center justify-center font-medium text-sm ${
                    currentVoiceData.gender === "female"
                      ? "bg-pink-500/10 border-pink-400/30 text-pink-300"
                      : "bg-blue-500/10 border-blue-400/30 text-blue-300"
                  }`}
                >
                  {currentVoiceData.name.charAt(0)}
                </div>
                {isChanging && (
                  <div className="absolute inset-0 rounded-lg border-2 border-[#22E58C]/50 animate-spin border-t-[#22E58C]" />
                )}
              </div>

              {/* Voice Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4 className="text-white font-medium">
                    {isChanging ? "Switching..." : currentVoiceData.name}
                  </h4>
                  <div className="flex items-center space-x-2">
                    <span
                      className={`text-xs px-2 py-0.5 rounded ${
                        currentVoiceData.gender === "female"
                          ? "bg-pink-500/20 text-pink-300"
                          : "bg-blue-500/20 text-blue-300"
                      }`}
                    >
                      {currentVoiceData.gender}
                    </span>
                    <svg
                      className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${
                        isOpen ? "rotate-180" : ""
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 9l-7 7-7-7"
                      />
                    </svg>
                  </div>
                </div>
                <p className="text-gray-400 text-sm mt-0.5">
                  {isChanging ? "Please wait..." : currentVoiceData.description}
                </p>
              </div>
            </div>
          </button>
        </div>

        {/* Voice Options Panel */}
        <div
          className={`transition-all duration-300 ease-out overflow-hidden ${
            isOpen ? "max-h-96 opacity-100" : "max-h-0 opacity-0"
          }`}
        >
          <div className="border-t border-[#22E58C]/8 px-5 py-4">
            {/* Simple Voice Grid */}
            <div className="space-y-3 max-h-64 overflow-y-auto custom-scrollbar">
              {AVAILABLE_VOICES.map((voice) => (
                <div key={voice.id} className="flex items-center space-x-3">
                  {/* Voice Selection Button */}
                  <button
                    onClick={() => handleVoiceChange(voice.id)}
                    disabled={isChanging}
                    className={`
                      flex-1 flex items-center space-x-3 p-3 rounded-lg border transition-all duration-200
                      ${
                        localCurrentVoice === voice.id
                          ? "bg-[#22E58C]/10 border-[#22E58C]/30 text-white"
                          : "bg-transparent border-gray-600/30 text-gray-300 hover:border-[#22E58C]/20 hover:bg-[#22E58C]/5"
                      }
                      ${isChanging ? "opacity-50 cursor-not-allowed" : ""}
                    `}
                  >
                    {/* Simple Avatar */}
                    <div
                      className={`w-8 h-8 rounded-lg border flex items-center justify-center text-xs font-medium ${
                        voice.gender === "female"
                          ? "bg-pink-500/10 border-pink-400/30 text-pink-300"
                          : "bg-blue-500/10 border-blue-400/30 text-blue-300"
                      }`}
                    >
                      {voice.name.charAt(0)}
                    </div>

                    {/* Voice Info */}
                    <div className="flex-1 text-left">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-sm">
                          {voice.name}
                        </span>
                        {localCurrentVoice === voice.id && (
                          <svg
                            className="w-4 h-4 text-[#22E58C]"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                              clipRule="evenodd"
                            />
                          </svg>
                        )}
                      </div>
                      <p className="text-gray-400 text-xs mt-0.5">
                        {voice.description}
                      </p>
                    </div>
                  </button>

                  {/* Preview Button */}
                  <button
                    onClick={() => handleVoicePreview(voice.id)}
                    disabled={!isConnected || previewingVoice === voice.id}
                    className={`
                      p-2 rounded-lg border transition-all duration-200
                      ${
                        previewingVoice === voice.id
                          ? "bg-[#22E58C]/20 border-[#22E58C]/30 text-[#22E58C] animate-pulse"
                          : "bg-transparent border-gray-600/30 text-gray-400 hover:border-[#22E58C]/30 hover:text-[#22E58C]"
                      }
                      ${!isConnected ? "opacity-50 cursor-not-allowed" : ""}
                    `}
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
                        d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1.586a1 1 0 01.707.293l1.414 1.414a1 1 0 01.293.707V13M15 10h-1.586a1 1 0 00-.707.293l-1.414 1.414a1 1 0 00-.293.707V13"
                      />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Simplified Footer */}
        <div className="px-5 py-3 border-t border-[#22E58C]/8">
          <div className="flex items-center justify-center">
            <span className="text-gray-400 text-xs">
              Powered by Deepgram AI
            </span>
          </div>
        </div>
      </div>

      {/* Custom Styles */}
      <style jsx>{`
        .custom-scrollbar {
          scrollbar-width: thin;
          scrollbar-color: #22e58c20 transparent;
        }
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #22e58c30;
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #22e58c50;
        }
        .line-clamp-2 {
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
      `}</style>
    </div>
  );
}
