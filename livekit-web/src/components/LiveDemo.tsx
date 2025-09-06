import dynamic from "next/dynamic";

const VoiceChat = dynamic(() => import("@/components/VoiceChat"), {
  ssr: false,
});

export default function LiveDemo() {
  return (
    <section id="demo" className="relative py-12 mx-2 md:mx-6">
      <div className="relative z-10 max-w-6xl mx-auto px-4">
        <div className="rounded-3xl overflow-hidden border border-white/10 bg-white/3 backdrop-blur">
          <div className="h-[80vh]">
            <VoiceChat embedded={true} />
          </div>
        </div>
      </div>
    </section>
  );
}
