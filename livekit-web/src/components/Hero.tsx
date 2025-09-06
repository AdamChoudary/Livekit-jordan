"use client";

import { motion } from "framer-motion";
import { useState } from "react";
import { IconArrowRight } from "@tabler/icons-react";
import { BackgroundRippleEffect } from "./ui/background-ripple-effect";
import { ShootingStars } from "./ui/shooting-stars";
import { StarsBackground } from "./ui/stars-background";

function AnimatedChartLine() {
  return (
    <div className="absolute bottom-0 left-0 right-0 h-[400px] pointer-events-none overflow-hidden">
      <svg
        className="absolute bottom-0 w-full h-full"
        viewBox="0 0 1440 400"
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id="chartGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="rgba(34, 229, 140, 0)" />
            <stop offset="5%" stopColor="rgba(34, 229, 140, 0.9)" />
            <stop offset="50%" stopColor="rgba(34, 229, 140, 0.9)" />
            <stop offset="100%" stopColor="rgba(34, 229, 140, 0)" />
          </linearGradient>

          <linearGradient id="chartGradient2" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="rgba(34, 229, 140, 0)" />
            <stop offset="8%" stopColor="rgba(34, 229, 140, 0.6)" />
            <stop offset="92%" stopColor="rgba(34, 229, 140, 0.6)" />
            <stop offset="100%" stopColor="rgba(34, 229, 140, 0)" />
          </linearGradient>

          <filter id="chartGlow" x="-100%" y="-100%" width="300%" height="300%">
            <feGaussianBlur stdDeviation="4" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          <filter id="pulseGlow" x="-100%" y="-100%" width="300%" height="300%">
            <feGaussianBlur stdDeviation="2" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
            <animate
              attributeName="stdDeviation"
              values="2;6;2"
              dur="3s"
              repeatCount="indefinite"
            />
          </filter>
        </defs>

        {/* Primary trading line - realistic bull market pattern */}
        <path
          d="M0,350 Q60,340 120,320 T240,280 Q300,260 360,240 T480,200 Q540,180 600,160 T720,120 Q780,100 840,90 T960,85 Q1020,88 1080,95 T1200,110 Q1260,120 1320,135 L1440,150"
          stroke="url(#chartGradient)"
          strokeWidth="2.5"
          fill="none"
          filter="url(#chartGlow)"
          strokeLinecap="round"
          opacity="1"
        >
          <animate
            attributeName="stroke-dasharray"
            values="0,2000;2000,0;0,2000"
            dur="12s"
            repeatCount="indefinite"
          />
          <animate
            attributeName="opacity"
            values="0.8;1;0.8"
            dur="3s"
            repeatCount="indefinite"
          />
        </path>

        {/* Secondary line - volatile trading pattern */}
        <path
          d="M0,380 Q80,360 160,340 T320,300 Q400,280 480,260 T640,220 Q720,200 800,185 T960,170 Q1040,175 1120,180 T1280,190 L1440,200"
          stroke="url(#chartGradient2)"
          strokeWidth="2"
          fill="none"
          filter="url(#pulseGlow)"
          strokeLinecap="round"
          opacity="0.7"
        >
          <animate
            attributeName="stroke-dasharray"
            values="0,1800;1800,0;0,1800"
            dur="10s"
            repeatCount="indefinite"
          />
        </path>

        {/* Tertiary support line - smooth trend */}
        <path
          d="M100,390 Q200,370 300,350 T500,310 Q600,290 700,270 T900,230 Q1000,210 1100,195 T1300,180 L1440,175"
          stroke="rgba(34, 229, 140, 0.4)"
          strokeWidth="1.5"
          fill="none"
          strokeLinecap="round"
          opacity="0.6"
        >
          <animate
            attributeName="opacity"
            values="0.4;0.8;0.4"
            dur="4s"
            repeatCount="indefinite"
          />
        </path>

        {/* Resistance line - upper boundary */}
        <path
          d="M0,280 Q120,270 240,260 T480,240 Q600,230 720,220 T960,200 Q1080,195 1200,190 T1440,185"
          stroke="rgba(34, 229, 140, 0.3)"
          strokeWidth="1"
          fill="none"
          strokeLinecap="round"
          opacity="0.5"
          strokeDasharray="8,4"
        >
          <animate
            attributeName="stroke-dashoffset"
            values="0;12;0"
            dur="6s"
            repeatCount="indefinite"
          />
        </path>

        {/* Volume indicator bars - subtle background */}
        <g opacity="0.15">
          {[
            45, 75, 30, 90, 55, 85, 40, 70, 60, 95, 35, 80, 50, 65, 25, 100, 45,
            75, 55, 85, 40, 70, 60, 35,
          ].map((height, i) => {
            const x = i * 60;
            return (
              <rect
                key={i}
                x={x}
                y={400 - height}
                width="3"
                height={height}
                fill="rgba(34, 229, 140, 0.3)"
              >
                <animate
                  attributeName="height"
                  values={`${height};${height * 1.5};${height}`}
                  dur="5s"
                  repeatCount="indefinite"
                  begin={`${i * 0.2}s`}
                />
              </rect>
            );
          })}
        </g>

        {/* Moving average line - smooth professional curve */}
        <path
          d="M0,340 Q150,330 300,320 T600,300 Q750,290 900,280 T1200,270 Q1320,265 1440,260"
          stroke="rgba(34, 229, 140, 0.25)"
          strokeWidth="1.2"
          fill="none"
          strokeLinecap="round"
          opacity="0.4"
        >
          <animate
            attributeName="stroke-width"
            values="1.2;2;1.2"
            dur="3s"
            repeatCount="indefinite"
          />
        </path>
      </svg>
    </div>
  );
}

// Compact Logo Component - Updated Branding
function CompactLogo() {
  return (
    <div className="flex items-center gap-3 m-3">
      <div className="w-8 h-8 bg-[#22E58C] rounded-lg flex items-center justify-center">
        <div className="w-4 h-4 bg-white rounded-sm" />
      </div>
      <span className="text-base font-semibold text-[#22E58C] tracking-[0.15em] uppercase">
        VOICEAI
      </span>
    </div>
  );
}

// Professional Header - Updated Branding
function ProfessionalHeader() {
  return (
    <header className="absolute top-0 left-0 right-0 ">
      <div className="max-w-[1200px] mx-auto px-6 h-16 flex items-center justify-between">
        <CompactLogo />
        <button className="text-sm font-medium text-[#A4B9B0] hover:text-[#E7F7F0] transition-colors duration-300">
          Sign in
        </button>
      </div>
    </header>
  );
}

// Trading Bot Tag - Updated Text
function TradingBotTag() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2, duration: 0.6, ease: [0.22, 0.61, 0.36, 1] }}
      className="inline-flex items-center gap-2 h-8 px-3 rounded-full border border-[#163A33]/40 bg-[rgba(22,58,51,0.35)] text-xs text-[#A4B9B0] font-medium"
    >
      <span>🎙️</span>
      <span>Voice Agents</span>
    </motion.div>
  );
}

// Hero Content - Updated Text
function HeroContent() {
  return (
    <div className="text-center max-w-[1200px] mx-auto px-6">
      {/* Tag */}
      <TradingBotTag />

      {/* Main Headline - Exact Size Match */}
      <motion.h1
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4, duration: 0.8, ease: [0.22, 0.61, 0.36, 1] }}
        className="font-bold text-5xl md:text-6xl lg:text-7xl text-[#E7F7F0] mt-4 mb-4 max-w-[800px] mx-auto leading-[1.1] tracking-[-0.02em]"
      >
        The Fastest and Secure
        <br />
        AI Voice Assistant.
      </motion.h1>

      {/* Subcopy - Perfect Sizing */}
      <motion.p
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6, duration: 0.8, ease: [0.22, 0.61, 0.36, 1] }}
        className="text-base leading-6 text-[#A4B9B0] max-w-[600px] mx-auto mb-8 font-normal"
      >
        Communicate faster and smarter with our secure AI voice agents. Enhance
        your conversations with real-time voice processing and automation.
      </motion.p>

      {/* CTA Button - Perfect Implementation */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8, duration: 0.8, ease: [0.22, 0.61, 0.36, 1] }}
        className="flex justify-center"
      >
        <button className="group relative inline-flex items-center gap-2 h-12 px-6 bg-[#22E58C] hover:bg-[#1ACB79] text-[#072517] font-semibold rounded-full transition-all duration-300 shadow-[0_8px_30px_rgba(34,229,140,0.25)] hover:shadow-[0_12px_40px_rgba(34,229,140,0.35)] hover:scale-[1.02] focus:outline-none focus:ring-2 focus:ring-[rgba(34,229,140,0.55)] focus:ring-offset-1 focus:ring-offset-black text-sm">
          <span>Try Free Trial</span>
          <IconArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform duration-300" />
          <div
            className="absolute inset-0 rounded-full bg-gradient-to-r from-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"
            style={{ boxShadow: "inset 0 1px 0 rgba(255,255,255,0.12)" }}
          />
        </button>
      </motion.div>
    </div>
  );
}

// Bottom Dock Navigation - Updated Tabs
function BottomDockNav({
  onNavigateToVoiceChat,
}: {
  onNavigateToVoiceChat?: () => void;
}) {
  const [activeTab, setActiveTab] = useState("Voice");

  const tabs = [
    { name: "Agents" },
    { name: "Models" },
    { name: "Voice" },
    { name: "Speech" },
    { name: "AI Assistant" },
  ];

  return (
    <motion.nav
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 1.2, duration: 0.5, ease: [0.22, 0.61, 0.36, 1] }}
      className="fixed bottom-6 left-1/2 transform -translate-x-1/2 w-[600px] max-w-[90vw] h-14 rounded-full border border-white/8 bg-[rgba(10,15,13,0.7)] backdrop-blur-xl shadow-[0_12px_40px_rgba(0,0,0,0.6)] flex items-center px-2 z-50"
    >
      {tabs.map((tab) => {
        const isActive = activeTab === tab.name;

        return (
          <button
            key={tab.name}
            onClick={() => setActiveTab(tab.name)}
            className={`relative flex-1 h-12 mx-0.5 rounded-full transition-all duration-300 flex items-center justify-center ${
              isActive
                ? "bg-[rgba(34,229,140,0.4)] text-white"
                : "text-[#A4B9B0] hover:text-[#E7F7F0] hover:bg-white/5"
            }`}
          >
            {isActive && (
              <motion.div
                layoutId="activeTab"
                className="absolute -top-2 left-1/2 transform -translate-x-1/2 w-8 h-1 bg-[#22E58C] rounded-full"
                transition={{ duration: 0.3, ease: [0.22, 0.61, 0.36, 1] }}
              />
            )}
            <span className="text-xs font-medium relative z-10">
              {tab.name}
            </span>
            {isActive && (
              <div className="absolute inset-0 rounded-full shadow-[0_0_20px_rgba(34,229,140,0.2)]" />
            )}
          </button>
        );
      })}

      {/* Circular arrow button */}
      <div className="ml-2 pl-2 border-l border-white/10">
        <button
          onClick={onNavigateToVoiceChat}
          className="w-12 h-12 rounded-full bg-[#22E58C] hover:bg-[#1ACB79] text-[#072517] font-bold transition-all duration-300 hover:scale-105 shadow-[0_6px_20px_rgba(34,229,140,0.4)] hover:shadow-[0_8px_25px_rgba(34,229,140,0.5)] flex items-center justify-center group"
        >
          <IconArrowRight className="w-5 h-5 group-hover:translate-x-0.5 transition-transform duration-300" />
        </button>
      </div>
    </motion.nav>
  );
}

export default function Hero({
  onNavigateToVoiceChat,
}: {
  onNavigateToVoiceChat?: () => void;
}) {
  return (
    <div className="min-h-screen w-full bg-[#0A0F0D] text-[#E7F7F0] font-[Sora] overflow-hidden rounded-3xl relative">
      {/* Background with layered effects - Exact Implementation */}
      <div className="pointer-events-none fixed inset-0">
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

      <StarsBackground starDensity={0.0002} className="opacity-60" />
      <ShootingStars
        minSpeed={15}
        maxSpeed={35}
        minDelay={800}
        maxDelay={3000}
        starColor="#22E58C"
        trailColor="#16A085"
        className="opacity-80"
      />

      <BackgroundRippleEffect rows={12} cols={32} cellSize={48} />

      {/* Animated Chart Line */}
      <AnimatedChartLine />

      {/* Header */}
      <ProfessionalHeader />

      {/* Main Content - Exact Center Positioning */}
      <div className="relative z-20 flex items-center justify-center min-h-screen pt-16 pb-32">
        <HeroContent />
      </div>

      {/* Bottom Dock Navigation */}
      <BottomDockNav onNavigateToVoiceChat={onNavigateToVoiceChat} />
    </div>
  );
}
