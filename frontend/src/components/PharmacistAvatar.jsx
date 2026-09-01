import { useEffect, useRef, useState } from "react";

/**
 * Premium AI Pharmacist Avatar with holographic ring and audio visualizer.
 *
 * To use a real photo: replace AVATAR_IMAGE_URL with your image URL.
 * Recommended: 512x512px, circular crop, professional pharmacist photo.
 */
const AVATAR_IMAGE_URL = null; // Set to a URL string to use a real photo

export default function PharmacistAvatar({ state = "idle", audioData = null }) {
  const canvasRef = useRef(null);
  const animFrameRef = useRef(null);
  const [time, setTime] = useState(0);

  // Animate the holographic ring and audio visualizer
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const size = 280;
    canvas.width = size * 2; // retina
    canvas.height = size * 2;
    canvas.style.width = `${size}px`;
    canvas.style.height = `${size}px`;
    ctx.scale(2, 2);
    const center = size / 2;
    const radius = 95;

    let t = 0;
    function draw() {
      t += 0.02;
      ctx.clearRect(0, 0, size, size);

      // Outer glow
      const glowRadius = radius + 20;
      const glow = ctx.createRadialGradient(center, center, radius, center, center, glowRadius);
      if (state === "talking") {
        glow.addColorStop(0, "rgba(16, 185, 129, 0.3)");
        glow.addColorStop(1, "rgba(16, 185, 129, 0)");
      } else if (state === "thinking") {
        glow.addColorStop(0, "rgba(139, 92, 246, 0.3)");
        glow.addColorStop(1, "rgba(139, 92, 246, 0)");
      } else {
        glow.addColorStop(0, "rgba(99, 102, 241, 0.15)");
        glow.addColorStop(1, "rgba(99, 102, 241, 0)");
      }
      ctx.beginPath();
      ctx.arc(center, center, glowRadius, 0, Math.PI * 2);
      ctx.fillStyle = glow;
      ctx.fill();

      // Holographic ring
      const barCount = 64;
      for (let i = 0; i < barCount; i++) {
        const angle = (i / barCount) * Math.PI * 2 - Math.PI / 2;

        // Audio-reactive height
        let barHeight = 3;
        if (state === "talking" && audioData && audioData.length > 0) {
          const dataIndex = Math.floor((i / barCount) * audioData.length);
          barHeight = 3 + (audioData[dataIndex] / 255) * 25;
        } else if (state === "talking") {
          barHeight = 3 + Math.sin(t * 3 + i * 0.3) * 8 + Math.random() * 5;
        } else if (state === "thinking") {
          barHeight = 3 + Math.sin(t * 2 + i * 0.15) * 4;
        } else {
          barHeight = 2 + Math.sin(t + i * 0.1) * 1.5;
        }

        const x1 = center + Math.cos(angle) * (radius + 4);
        const y1 = center + Math.sin(angle) * (radius + 4);
        const x2 = center + Math.cos(angle) * (radius + 4 + barHeight);
        const y2 = center + Math.sin(angle) * (radius + 4 + barHeight);

        // Color based on state
        let hue;
        if (state === "talking") {
          hue = 160 + Math.sin(t + i * 0.1) * 20; // emerald/teal
        } else if (state === "thinking") {
          hue = 270 + Math.sin(t * 1.5 + i * 0.1) * 30; // violet
        } else {
          hue = 230 + Math.sin(t * 0.5 + i * 0.05) * 20; // blue/indigo
        }

        const alpha = state === "idle" ? 0.3 : 0.6;
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.strokeStyle = `hsla(${hue}, 80%, 65%, ${alpha})`;
        ctx.lineWidth = 2.5;
        ctx.lineCap = "round";
        ctx.stroke();
      }

      // Inner ring (subtle border)
      ctx.beginPath();
      ctx.arc(center, center, radius + 1, 0, Math.PI * 2);
      ctx.strokeStyle = state === "talking"
        ? "rgba(16, 185, 129, 0.4)"
        : state === "thinking"
          ? "rgba(139, 92, 246, 0.4)"
          : "rgba(99, 102, 241, 0.2)";
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Rotating accent dot
      const dotAngle = t * (state === "thinking" ? 2 : 0.5);
      const dotX = center + Math.cos(dotAngle) * (radius + 2);
      const dotY = center + Math.sin(dotAngle) * (radius + 2);
      ctx.beginPath();
      ctx.arc(dotX, dotY, 3, 0, Math.PI * 2);
      ctx.fillStyle = state === "talking"
        ? "rgba(52, 211, 153, 0.9)"
        : state === "thinking"
          ? "rgba(167, 139, 250, 0.9)"
          : "rgba(129, 140, 248, 0.5)";
      ctx.fill();

      animFrameRef.current = requestAnimationFrame(draw);
    }

    draw();
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [state, audioData]);

  return (
    <div className="relative flex items-center justify-center">
      {/* Canvas ring visualizer */}
      <canvas ref={canvasRef} className="absolute z-10 pointer-events-none" />

      {/* Avatar circle */}
      <div className="w-[190px] h-[190px] rounded-full overflow-hidden relative z-0 shadow-2xl">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-slate-700 via-slate-800 to-slate-900" />

        {AVATAR_IMAGE_URL ? (
          <img
            src={AVATAR_IMAGE_URL}
            alt="AI Pharmacist"
            className="absolute inset-0 w-full h-full object-cover"
          />
        ) : (
          /* Professional pharmacist silhouette */
          <svg
            className="absolute inset-0 w-full h-full"
            viewBox="0 0 200 200"
            fill="none"
          >
            {/* Subtle background glow */}
            <defs>
              <radialGradient id="bgGlow" cx="50%" cy="35%" r="60%">
                <stop offset="0%" stopColor="rgba(99,102,241,0.15)" />
                <stop offset="100%" stopColor="transparent" />
              </radialGradient>
              <linearGradient id="bodyGrad" x1="100" y1="80" x2="100" y2="200">
                <stop offset="0%" stopColor="rgba(255,255,255,0.9)" />
                <stop offset="100%" stopColor="rgba(200,210,230,0.7)" />
              </linearGradient>
              <linearGradient id="skinGrad" x1="100" y1="30" x2="100" y2="85">
                <stop offset="0%" stopColor="#e8c4a0" />
                <stop offset="100%" stopColor="#d4a574" />
              </linearGradient>
              <linearGradient id="hairGrad" x1="70" y1="15" x2="130" y2="60">
                <stop offset="0%" stopColor="#2c1810" />
                <stop offset="100%" stopColor="#4a2c1a" />
              </linearGradient>
            </defs>

            <rect width="200" height="200" fill="url(#bgGlow)" />

            {/* Hair - back */}
            <ellipse cx="100" cy="50" rx="42" ry="45" fill="url(#hairGrad)" />
            <path d="M58 55 Q55 80 62 100 Q65 95 68 85 Q65 70 65 55Z" fill="url(#hairGrad)" />
            <path d="M142 55 Q145 80 138 100 Q135 95 132 85 Q135 70 135 55Z" fill="url(#hairGrad)" />

            {/* Neck */}
            <rect x="90" y="78" width="20" height="18" rx="4" fill="url(#skinGrad)" />

            {/* Face */}
            <ellipse cx="100" cy="55" rx="32" ry="36" fill="url(#skinGrad)" />

            {/* Hair - front/bangs */}
            <path d="M68 42 Q75 20 100 18 Q125 20 132 42 Q128 30 100 28 Q72 30 68 42Z" fill="url(#hairGrad)" />
            <path d="M68 45 Q70 35 78 30 Q72 40 70 48Z" fill="url(#hairGrad)" opacity="0.7" />

            {/* Eyes */}
            <ellipse cx="86" cy="52" rx="5" ry="3.5" fill="white" />
            <ellipse cx="114" cy="52" rx="5" ry="3.5" fill="white" />
            <circle cx="87" cy="52" r="2.5" fill="#3b2518" />
            <circle cx="115" cy="52" r="2.5" fill="#3b2518" />
            <circle cx="87.5" cy="51.5" r="0.8" fill="white" />
            <circle cx="115.5" cy="51.5" r="0.8" fill="white" />

            {/* Eyebrows */}
            <path d="M78 46 Q86 43 94 45" stroke="#3b2518" strokeWidth="1.5" fill="none" strokeLinecap="round" />
            <path d="M106 45 Q114 43 122 46" stroke="#3b2518" strokeWidth="1.5" fill="none" strokeLinecap="round" />

            {/* Nose */}
            <path d="M98 56 Q100 62 102 56" stroke="#c4956e" strokeWidth="1" fill="none" />

            {/* Mouth / smile */}
            <path d="M90 67 Q100 73 110 67" stroke="#c07060" strokeWidth="1.5" fill="none" strokeLinecap="round" />
            <path d="M93 67 Q100 71 107 67" fill="#d08070" opacity="0.3" />

            {/* Body / lab coat */}
            <path
              d="M60 200 L60 140 Q60 110 75 100 L85 95 Q100 90 115 95 L125 100 Q140 110 140 140 L140 200Z"
              fill="url(#bodyGrad)"
            />

            {/* Coat lapels / V-neck */}
            <path d="M85 95 L100 125 L115 95" stroke="rgba(100,116,139,0.3)" strokeWidth="1.5" fill="none" />

            {/* Inner shirt */}
            <path d="M88 96 L100 118 L112 96" fill="rgba(99,102,241,0.15)" />

            {/* Stethoscope */}
            <path d="M82 100 Q72 115 76 140" stroke="rgba(100,116,139,0.5)" strokeWidth="2" fill="none" strokeLinecap="round" />
            <circle cx="76" cy="142" r="4" fill="rgba(100,116,139,0.4)" />
            <circle cx="76" cy="142" r="2" fill="rgba(100,116,139,0.6)" />

            {/* Name badge */}
            <rect x="110" y="120" width="20" height="12" rx="2" fill="rgba(99,102,241,0.2)" stroke="rgba(99,102,241,0.3)" strokeWidth="0.5" />
            <line x1="113" y1="124" x2="127" y2="124" stroke="rgba(99,102,241,0.3)" strokeWidth="0.8" />
            <line x1="113" y1="128" x2="123" y2="128" stroke="rgba(99,102,241,0.3)" strokeWidth="0.8" />

            {/* Medical cross on pocket */}
            <rect x="95" y="145" width="3" height="12" rx="1" fill="rgba(99,102,241,0.15)" />
            <rect x="91" y="148" width="11" height="3" rx="1" fill="rgba(99,102,241,0.15)" />
          </svg>
        )}

        {/* Overlay shimmer */}
        <div
          className="absolute inset-0 opacity-20"
          style={{
            background: "linear-gradient(135deg, transparent 40%, rgba(255,255,255,0.1) 50%, transparent 60%)",
            animation: "shimmer 3s ease-in-out infinite",
          }}
        />
      </div>

      {/* State indicator dot */}
      <div className="absolute -bottom-1 z-20 flex items-center gap-1.5 bg-slate-900/80 backdrop-blur-sm px-3 py-1 rounded-full border border-slate-700/50">
        <div
          className={`w-2 h-2 rounded-full ${
            state === "talking"
              ? "bg-emerald-400 animate-pulse"
              : state === "thinking"
                ? "bg-violet-400 animate-pulse"
                : "bg-indigo-400"
          }`}
        />
        <span className="text-[10px] font-medium text-slate-300">
          {state === "talking" ? "Hovorím" : state === "thinking" ? "Premýšľam" : "Online"}
        </span>
      </div>
    </div>
  );
}
