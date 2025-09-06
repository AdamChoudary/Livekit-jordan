export default function HowItWorks() {
  const steps = [
    { t: "Join", d: "Secure WebRTC room via LiveKit with token auth." },
    { t: "Listen", d: "Low‑latency STT streams user speech in real time." },
    {
      t: "Think",
      d: "Agent plans, retrieves memory, and decides next action.",
    },
    { t: "Speak", d: "Neural TTS streams prosody‑rich speech back instantly." },
  ];

  return (
    <section className="relative py-16 md:py-24 mx-2 md:mx-6">
      <div className="relative z-10 max-w-5xl mx-auto px-6">
        <h2 className="text-3xl md:text-4xl font-semibold text-white text-center mb-12">
          How it works
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {steps.map((s, i) => (
            <div
              key={i}
              className="rounded-2xl bg-white/3 border border-white/10 p-5 text-center backdrop-blur"
            >
              <div className="text-xs tracking-widest text-slate-300 mb-2">
                STEP {i + 1}
              </div>
              <div className="text-white font-medium">{s.t}</div>
              <div className="text-slate-300 text-sm mt-2">{s.d}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
