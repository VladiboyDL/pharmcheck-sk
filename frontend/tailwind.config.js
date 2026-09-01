/**
 * Tokens lifted from avatarai.com so the product reads as the same company:
 * pure black ground, one blue accent, hierarchy carried by white opacity rather
 * than by a grey ramp, Figtree with tight negative tracking, Fragment Mono for data.
 *
 * Contrast on black, measured: text 21:1, text-2 9.9:1, text-3 5.3:1 — all pass for
 * body copy. text-4 is 2.4:1 and is decoration only; never put meaning in it.
 * On an accent fill, black text is 5.4:1 where white is 3.9:1, so accent buttons
 * carry black labels.
 */
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#000000",
        panel: "#0B0B14",
        panel2: "#080808",
        surface: "rgba(255,255,255,0.03)",
        surface2: "rgba(255,255,255,0.06)",
        hairline: "rgba(255,255,255,0.10)",
        hairline2: "rgba(255,255,255,0.16)",
        txt: "#FFFFFF",
        txt2: "rgba(255,255,255,0.70)",
        txt3: "rgba(255,255,255,0.50)",
        txt4: "rgba(255,255,255,0.30)",
        brand: "#2E7BFF",
        brandDeep: "#1140ED",
        ok: "#34D399",
        warn: "#FBBF24",
        bad: "#FF5F56",
      },
      fontFamily: {
        sans: ["Figtree", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["'Fragment Mono'", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      borderRadius: {
        card: "20px",
        pill: "100px",
        sm2: "10px",
      },
      letterSpacing: {
        tighter2: "-0.03em",
        tight2: "-0.025em",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "ping-slower": "ping 3s cubic-bezier(0, 0, 0.2, 1) infinite",
      },
    },
  },
  plugins: [],
};
