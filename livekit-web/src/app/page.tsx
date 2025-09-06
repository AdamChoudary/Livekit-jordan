"use client";
import { useState } from "react";
import Hero from "@/components/Hero";
import VoiceChat from "@/components/VoiceChat";

export default function Home() {
  const [showVoiceChat, setShowVoiceChat] = useState(false);

  if (showVoiceChat) {
    return <VoiceChat onBack={() => setShowVoiceChat(false)} />;
  }

  return <Hero onNavigateToVoiceChat={() => setShowVoiceChat(true)} />;
}
