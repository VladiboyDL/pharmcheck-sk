import { useEffect, useRef, useState } from "react";
import { getDemoCards, readCard, verifyBiometric } from "../api/client";

/**
 * Two-factor patient identity check at the dispensing window:
 *   1. insurance card read (simulated NFC)
 *   2. 1:1 face match against the insurer's reference photo (simulated match,
 *      real camera feed so the operator can see liveness capture)
 */
export default function IdentityGate({ onVerified, onReset }) {
  const [cards, setCards] = useState([]);
  const [stage, setStage] = useState("card"); // card | reading | biometric | scanning | done
  const [patient, setPatient] = useState(null);
  const [cardMeta, setCardMeta] = useState(null);
  const [biometric, setBiometric] = useState(null);
  const [forceMismatch, setForceMismatch] = useState(false);
  const [error, setError] = useState(null);
  const [score, setScore] = useState(0);

  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const [cameraState, setCameraState] = useState("idle"); // idle | live | denied

  useEffect(() => {
    getDemoCards()
      .then((d) => setCards(d.cards))
      .catch(() => setError("Backend nie je dostupný"));
    return () => stopCamera();
  }, []);

  function stopCamera() {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
  }

  async function startCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: "user" },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play().catch(() => {});
      }
      setCameraState("live");
    } catch {
      setCameraState("denied");
    }
  }

  async function handleCardTap(cardId) {
    setError(null);
    setStage("reading");
    try {
      await new Promise((r) => setTimeout(r, 900)); // NFC handshake
      const data = await readCard(cardId);
      setPatient(data.patient);
      setCardMeta(data);
      setStage("biometric");
      startCamera();
    } catch (e) {
      setError(e.message);
      setStage("card");
    }
  }

  async function handleFaceScan() {
    if (!patient) return;
    setStage("scanning");
    setScore(0);

    const result = await verifyBiometric(patient.card_id, {
      frameSignature: `f${Math.floor(Date.now() / 1000)}`,
      forceMismatch,
    });

    // Count the score up while the scan animation runs
    const target = result.match_score ?? 0;
    const steps = 28;
    for (let i = 1; i <= steps; i++) {
      await new Promise((r) => setTimeout(r, 55));
      setScore(Number(((target * i) / steps).toFixed(1)));
    }

    setBiometric(result);
    setStage("done");
    stopCamera();
    onVerified?.({ patient, biometric: result, cardMeta });
  }

  function reset() {
    stopCamera();
    setStage("card");
    setPatient(null);
    setCardMeta(null);
    setBiometric(null);
    setScore(0);
    setCameraState("idle");
    setError(null);
    onReset?.();
  }

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950 overflow-hidden">
      <div className="flex items-center justify-between px-5 py-3 border-b border-slate-800 bg-slate-900/60">
        <div className="flex items-center gap-2.5">
          <span className="w-6 h-6 rounded-md bg-cyan-500/15 text-cyan-300 grid place-items-center text-[11px] font-bold">
            1
          </span>
          <h3 className="text-sm font-semibold text-slate-100">Overenie totožnosti pacienta</h3>
        </div>
        <div className="flex items-center gap-2">
          <StepDot active={["card", "reading"].includes(stage)} done={!!patient} label="Karta" />
          <div className="w-5 h-px bg-slate-700" />
          <StepDot active={["biometric", "scanning"].includes(stage)} done={!!biometric} label="Tvár" />
        </div>
      </div>

      <div className="p-5">
        {error && (
          <div className="mb-4 rounded-lg border border-red-900 bg-red-950/60 px-3 py-2 text-xs text-red-300">
            {error}
          </div>
        )}

        {/* ── Stage: waiting for card ─────────────────────────────────────── */}
        {(stage === "card" || stage === "reading") && (
          <div>
            <div className="flex flex-col items-center py-6">
              <div className="relative w-20 h-20 grid place-items-center">
                <span
                  className={`absolute inset-0 rounded-full border border-cyan-500/40 ${
                    stage === "reading" ? "animate-ping" : "animate-ping-slower"
                  }`}
                />
                <span className="absolute inset-3 rounded-full border border-cyan-500/25" />
                <svg className="w-8 h-8 text-cyan-300 relative" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <rect x="2" y="5" width="20" height="14" rx="2" strokeWidth="1.5" />
                  <path strokeWidth="1.5" strokeLinecap="round" d="M2 10h20M6 15h4" />
                </svg>
              </div>
              <p className="mt-3 text-sm font-medium text-slate-200">
                {stage === "reading" ? "Načítavam kartu…" : "Priložte kartu poistenca"}
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">
                {stage === "reading" ? "NFC / ISO 14443-A" : "Bezkontaktné načítanie NFC"}
              </p>
            </div>

            <div className="mt-2 pt-4 border-t border-slate-800">
              <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-2.5">
                Kliknutím simulujete priloženie karty
              </p>
              <div className="grid gap-2">
                {cards.map((c) => (
                  <button
                    key={c.card_id}
                    disabled={stage === "reading"}
                    onClick={() => handleCardTap(c.card_id)}
                    className="text-left rounded-lg border border-slate-800 bg-slate-900/60 hover:border-cyan-700 hover:bg-slate-900 disabled:opacity-40 px-3 py-2.5 transition-colors group"
                  >
                    <div className="flex items-baseline justify-between gap-2">
                      <span className="text-sm font-medium text-slate-100 group-hover:text-cyan-200">
                        {c.name}
                      </span>
                      <span className="text-[10px] text-slate-500 tabular-nums">{c.age} r.</span>
                    </div>
                    <p className="text-[10px] text-slate-500 mt-0.5 line-clamp-1">{c.summary}</p>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── Stage: biometric ─────────────────────────────────────────────── */}
        {(stage === "biometric" || stage === "scanning") && patient && (
          <div className="grid gap-5 md:grid-cols-[minmax(0,1fr)_260px]">
            <div>
              <div className="relative rounded-xl overflow-hidden bg-slate-900 border border-slate-800 aspect-[4/3]">
                <video
                  ref={videoRef}
                  muted
                  playsInline
                  className={`w-full h-full object-cover ${cameraState === "live" ? "" : "opacity-0"}`}
                  style={{ transform: "scaleX(-1)" }}
                />
                {cameraState !== "live" && (
                  <div className="absolute inset-0 grid place-items-center text-center px-6">
                    <div>
                      <svg className="w-10 h-10 text-slate-700 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <circle cx="12" cy="9" r="3.2" strokeWidth="1.5" />
                        <path strokeWidth="1.5" strokeLinecap="round" d="M5.5 19a6.5 6.5 0 0113 0" />
                      </svg>
                      <p className="text-[11px] text-slate-500 mt-2">
                        {cameraState === "denied"
                          ? "Kamera nie je dostupná — overenie beží v simulovanom režime"
                          : "Spúšťam kameru…"}
                      </p>
                    </div>
                  </div>
                )}

                {/* Face frame + sweep */}
                <div className="absolute inset-0 pointer-events-none">
                  <div
                    className={`absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-40 h-52 rounded-[45%] border-2 transition-colors ${
                      stage === "scanning" ? "border-cyan-400" : "border-slate-600/70"
                    }`}
                  />
                  {stage === "scanning" && (
                    <div className="absolute left-0 right-0 h-0.5 bg-cyan-400/80 shadow-[0_0_12px_2px_rgba(34,211,238,0.6)] animate-[scanSweep_1.6s_ease-in-out_infinite]" />
                  )}
                  <Corner className="top-3 left-3 border-t-2 border-l-2" />
                  <Corner className="top-3 right-3 border-t-2 border-r-2" />
                  <Corner className="bottom-3 left-3 border-b-2 border-l-2" />
                  <Corner className="bottom-3 right-3 border-b-2 border-r-2" />
                </div>

                {stage === "scanning" && (
                  <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between rounded-lg bg-slate-950/85 backdrop-blur px-3 py-2">
                    <span className="text-[10px] uppercase tracking-wider text-cyan-300">
                      Porovnávam s referenčnou fotografiou
                    </span>
                    <span className="text-sm font-bold text-cyan-300 tabular-nums">{score.toFixed(1)}%</span>
                  </div>
                )}
              </div>

              <div className="mt-3 flex items-center gap-3">
                <button
                  onClick={handleFaceScan}
                  disabled={stage === "scanning"}
                  className="flex-1 rounded-lg bg-cyan-500 hover:bg-cyan-400 disabled:bg-slate-700 disabled:text-slate-400 text-slate-950 font-semibold text-sm py-2.5 transition-colors"
                >
                  {stage === "scanning" ? "Overujem…" : "Spustiť overenie tváre"}
                </button>
                <label className="flex items-center gap-1.5 text-[11px] text-slate-500 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={forceMismatch}
                    onChange={(e) => setForceMismatch(e.target.checked)}
                    className="accent-red-500"
                  />
                  simulovať nezhodu
                </label>
              </div>
            </div>

            <PatientCard patient={patient} cardMeta={cardMeta} onReset={reset} />
          </div>
        )}

        {/* ── Stage: done ──────────────────────────────────────────────────── */}
        {stage === "done" && patient && biometric && (
          <div className="grid gap-5 md:grid-cols-[minmax(0,1fr)_260px]">
            <div
              className={`rounded-xl border p-5 ${
                biometric.verified
                  ? "border-emerald-800 bg-emerald-950/40"
                  : "border-red-800 bg-red-950/40"
              }`}
            >
              <div className="flex items-start gap-3">
                <div
                  className={`w-9 h-9 rounded-lg grid place-items-center flex-shrink-0 ${
                    biometric.verified ? "bg-emerald-500/15 text-emerald-300" : "bg-red-500/15 text-red-300"
                  }`}
                >
                  {biometric.verified ? (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeWidth="2.2" strokeLinecap="round" d="M6 6l12 12M18 6L6 18" />
                    </svg>
                  )}
                </div>
                <div className="min-w-0">
                  <p className={`font-semibold ${biometric.verified ? "text-emerald-200" : "text-red-200"}`}>
                    {biometric.verified ? "Totožnosť potvrdená" : "Totožnosť nepotvrdená"}
                  </p>
                  <p className="text-xs text-slate-400 mt-0.5">{biometric.reason}</p>
                  {biometric.escalation && (
                    <p className="text-xs text-red-300 mt-2 font-medium">{biometric.escalation}</p>
                  )}
                </div>
              </div>

              <dl className="mt-4 grid grid-cols-2 gap-3 text-xs">
                <Metric
                  label="Zhoda tváre"
                  value={biometric.match_score != null ? `${biometric.match_score} %` : "—"}
                  tone={biometric.verified ? "good" : "bad"}
                />
                <Metric
                  label="Detekcia živosti"
                  value={biometric.liveness ? `${biometric.liveness.score} %` : "—"}
                  tone={biometric.liveness?.passed ? "good" : "bad"}
                />
                <Metric label="Prah zhody" value={biometric.threshold ? `${biometric.threshold} %` : "—"} />
                <Metric label="Referencia" value={biometric.matched_name || "—"} />
              </dl>

              <p className="mt-4 text-[10px] text-slate-500 leading-relaxed">
                Simulované overenie. V produkcii sa porovnáva s fotografiou poistenca zo systému
                zdravotnej poisťovne; snímka sa nikde neukladá.
              </p>
            </div>

            <PatientCard patient={patient} cardMeta={cardMeta} onReset={reset} />
          </div>
        )}
      </div>

      <style>{`
        @keyframes scanSweep {
          0%   { top: 12%; opacity: 0.2; }
          50%  { top: 82%; opacity: 1; }
          100% { top: 12%; opacity: 0.2; }
        }
      `}</style>
    </div>
  );
}

function Corner({ className }) {
  return <span className={`absolute w-5 h-5 border-cyan-500/50 ${className}`} />;
}

function StepDot({ active, done, label }) {
  return (
    <div className="flex items-center gap-1.5">
      <span
        className={`w-1.5 h-1.5 rounded-full ${
          done ? "bg-emerald-400" : active ? "bg-cyan-400 animate-pulse" : "bg-slate-700"
        }`}
      />
      <span className={`text-[10px] ${done || active ? "text-slate-300" : "text-slate-600"}`}>{label}</span>
    </div>
  );
}

function Metric({ label, value, tone }) {
  const colour = tone === "good" ? "text-emerald-300" : tone === "bad" ? "text-red-300" : "text-slate-200";
  return (
    <div>
      <dt className="text-[10px] uppercase tracking-wider text-slate-500">{label}</dt>
      <dd className={`font-semibold tabular-nums ${colour}`}>{value}</dd>
    </div>
  );
}

function PatientCard({ patient, cardMeta, onReset }) {
  const flags = [];
  if (patient.pregnant)
    flags.push({ text: `Gravidita — ${patient.pregnancy_week}. týždeň`, tone: "amber" });
  if (patient.egfr != null && patient.egfr < 60)
    flags.push({ text: `Znížená renálna funkcia — eGFR ${patient.egfr}`, tone: "amber" });
  if (patient.allergies?.length)
    flags.push({ text: `Alergia: ${patient.allergies.join(", ")}`, tone: "red" });
  if (patient.guardian) flags.push({ text: `Zákonný zástupca: ${patient.guardian}`, tone: "slate" });

  return (
    <aside className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 h-fit">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="font-semibold text-slate-100 leading-tight">{patient.name}</p>
          <p className="text-[11px] text-slate-500 tabular-nums">{patient.birth_id_masked}</p>
        </div>
        <button onClick={onReset} className="text-[10px] text-slate-500 hover:text-slate-300 underline">
          zmeniť
        </button>
      </div>

      <dl className="mt-3 space-y-1.5 text-xs">
        <Row label="Vek" value={`${patient.age} rokov`} />
        <Row label="Hmotnosť" value={patient.weight_kg ? `${patient.weight_kg} kg` : "—"} />
        <Row
          label="eGFR"
          value={patient.egfr != null ? `${patient.egfr} ml/min` : "—"}
          highlight={patient.egfr != null && patient.egfr < 60}
        />
        <Row label="Poisťovňa" value={patient.insurer} />
      </dl>

      {patient.chronic?.length > 0 && (
        <div className="mt-3 pt-3 border-t border-slate-800">
          <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1.5">Chronická liečba</p>
          <ul className="space-y-0.5">
            {patient.chronic.map((c) => (
              <li key={c} className="text-[11px] text-slate-400">
                {c}
              </li>
            ))}
          </ul>
        </div>
      )}

      {flags.length > 0 && (
        <div className="mt-3 pt-3 border-t border-slate-800 space-y-1.5">
          {flags.map((f) => (
            <p
              key={f.text}
              className={`text-[11px] rounded px-2 py-1 ${
                f.tone === "red"
                  ? "bg-red-950/60 text-red-300"
                  : f.tone === "amber"
                  ? "bg-amber-950/50 text-amber-300"
                  : "bg-slate-800/60 text-slate-400"
              }`}
            >
              {f.text}
            </p>
          ))}
        </div>
      )}

      {cardMeta && (
        <p className="mt-3 pt-3 border-t border-slate-800 text-[10px] text-slate-600">
          {cardMeta.channel} · karta platná · poistenie aktívne
        </p>
      )}
    </aside>
  );
}

function Row({ label, value, highlight }) {
  return (
    <div className="flex items-baseline justify-between gap-2">
      <dt className="text-slate-500">{label}</dt>
      <dd className={`tabular-nums text-right ${highlight ? "text-amber-300 font-semibold" : "text-slate-300"}`}>
        {value}
      </dd>
    </div>
  );
}
