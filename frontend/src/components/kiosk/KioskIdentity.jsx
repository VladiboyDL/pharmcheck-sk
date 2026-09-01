import { useEffect, useRef, useState } from "react";
import { getDemoCards, readCard, verifyBiometric } from "../../api/client";
import { Screen, Title, BigButton } from "./KioskShell";

/** Card tap, then face. One instruction on screen at a time. */
export default function KioskIdentity({ onDone }) {
  const [cards, setCards] = useState([]);
  const [stage, setStage] = useState("card"); // card | reading | face | scanning
  const [patient, setPatient] = useState(null);
  const [score, setScore] = useState(0);
  const [cameraOk, setCameraOk] = useState(false);
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    getDemoCards().then((d) => setCards(d.cards)).catch(() => {});
    return () => streamRef.current?.getTracks().forEach((t) => t.stop());
  }, []);

  async function tapCard(cardId) {
    setStage("reading");
    await new Promise((r) => setTimeout(r, 900));
    const data = await readCard(cardId);
    setPatient(data.patient);
    setStage("face");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play().catch(() => {});
      }
      setCameraOk(true);
    } catch {
      setCameraOk(false);
    }
  }

  async function scan() {
    setStage("scanning");
    const result = await verifyBiometric(patient.card_id, { frameSignature: `k${Date.now()}` });
    const target = result.match_score ?? 0;
    for (let i = 1; i <= 24; i++) {
      await new Promise((r) => setTimeout(r, 50));
      setScore(Number(((target * i) / 24).toFixed(1)));
    }
    streamRef.current?.getTracks().forEach((t) => t.stop());
    onDone({ patient, biometric: result });
  }

  if (stage === "card" || stage === "reading") {
    return (
      <Screen
        footer={
          <div>
            <p className="text-center text-[11px] uppercase tracking-wider text-slate-600 mb-3">
              Demo — vyberte pacienta
            </p>
            <div className="grid gap-2 sm:grid-cols-3">
              {cards.map((c) => (
                <button
                  key={c.card_id}
                  disabled={stage === "reading"}
                  onClick={() => tapCard(c.card_id)}
                  className="rounded-xl border border-slate-800 bg-slate-900/60 hover:border-cyan-700 disabled:opacity-40 px-3 py-2.5 text-left transition-colors"
                >
                  <span className="block text-sm text-slate-200">{c.name}</span>
                  <span className="block text-[11px] text-slate-500">{c.age} rokov</span>
                </button>
              ))}
            </div>
          </div>
        }
      >
        <div className="flex flex-col items-center">
          <div className="relative w-32 h-32 grid place-items-center mb-8">
            <span className="absolute inset-0 rounded-full border-2 border-cyan-500/30 animate-ping-slower" />
            <span className="absolute inset-5 rounded-full border border-cyan-500/20" />
            <svg className="w-14 h-14 text-cyan-300 relative" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <rect x="2" y="5" width="20" height="14" rx="2" strokeWidth="1.4" />
              <path strokeWidth="1.4" strokeLinecap="round" d="M2 10h20M6 15h4" />
            </svg>
          </div>
          <Title sub={stage === "reading" ? "Čítam údaje z karty" : "Stačí ju priložiť k čítačke"}>
            {stage === "reading" ? "Načítavam kartu…" : "Priložte kartu poistenca"}
          </Title>
        </div>
      </Screen>
    );
  }

  return (
    <Screen
      footer={
        <BigButton onClick={scan} disabled={stage === "scanning"} full>
          {stage === "scanning" ? `Overujem… ${score.toFixed(0)} %` : "Overiť totožnosť"}
        </BigButton>
      }
    >
      <div className="flex flex-col items-center">
        <div className="relative w-56 h-72 rounded-[2rem] overflow-hidden bg-slate-900 border border-slate-800 mb-7">
          <video
            ref={videoRef}
            muted
            playsInline
            className={`w-full h-full object-cover ${cameraOk ? "" : "opacity-0"}`}
            style={{ transform: "scaleX(-1)" }}
          />
          {!cameraOk && (
            <div className="absolute inset-0 grid place-items-center">
              <svg className="w-16 h-16 text-slate-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle cx="12" cy="9" r="3.2" strokeWidth="1.3" />
                <path strokeWidth="1.3" strokeLinecap="round" d="M5.5 19a6.5 6.5 0 0113 0" />
              </svg>
            </div>
          )}
          <div
            className={`absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-36 h-48 rounded-[45%] border-2 transition-colors ${
              stage === "scanning" ? "border-cyan-400" : "border-slate-600/60"
            }`}
          />
          {stage === "scanning" && (
            <div className="absolute left-0 right-0 h-0.5 bg-cyan-400/80 shadow-[0_0_14px_3px_rgba(34,211,238,0.55)] animate-[kioskSweep_1.5s_ease-in-out_infinite]" />
          )}
        </div>
        <Title sub={`Vitajte, ${patient.name.split(" ")[0]}. Pozrite sa prosím do kamery.`}>
          Overenie totožnosti
        </Title>
      </div>
      <style>{`@keyframes kioskSweep{0%{top:14%}50%{top:80%}100%{top:14%}}`}</style>
    </Screen>
  );
}
