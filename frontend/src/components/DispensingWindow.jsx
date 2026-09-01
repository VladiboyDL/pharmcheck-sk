import { useEffect, useState } from "react";
import IdentityGate from "./IdentityGate";
import IntakeInterview from "./IntakeInterview";
import DispenseResult from "./DispenseResult";
import { getScenario, verifyDispense } from "../api/client";

/**
 * The dispensing window: identity → prescription → verification decision.
 * This is the flow that replaces the manual counter check.
 */
export default function DispensingWindow({ onSessionResult }) {
  const [identity, setIdentity] = useState(null);
  const [scenario, setScenario] = useState(null);
  const [text, setText] = useState("");
  const [intakeAnswers, setIntakeAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const identityOk = identity?.biometric?.verified === true;

  useEffect(() => {
    if (!identity?.patient?.card_id) return;
    getScenario(identity.patient.card_id)
      .then((s) => {
        setScenario(s);
        setText(s?.text ?? "");
      })
      .catch(() => {});
  }, [identity?.patient?.card_id]);

  async function handleVerify() {
    setLoading(true);
    setError(null);
    try {
      const data = await verifyDispense({
        cardId: identity.patient.card_id,
        prescriptionText: text,
        identityVerified: identityOk,
        intake: intakeAnswers,
      });
      setResult(data);
      onSessionResult?.(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  function fullReset() {
    setIdentity(null);
    setScenario(null);
    setText("");
    setIntakeAnswers({});
    setResult(null);
    setError(null);
  }

  if (result) {
    return (
      <div className="space-y-4">
        <Header />
        <DispenseResult data={result} onReset={fullReset} />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Header />

      <IdentityGate onVerified={setIdentity} onReset={() => setIdentity(null)} />

      {/* ── Step 2: prescription ──────────────────────────────────────────── */}
      <div
        className={`rounded-2xl border bg-slate-950 overflow-hidden transition-opacity ${
          identity ? "border-slate-800 opacity-100" : "border-slate-900 opacity-40 pointer-events-none"
        }`}
      >
        <div className="flex items-center justify-between px-5 py-3 border-b border-slate-800 bg-slate-900/60">
          <div className="flex items-center gap-2.5">
            <span className="w-6 h-6 rounded-md bg-cyan-500/15 text-cyan-300 grid place-items-center text-[11px] font-bold">
              2
            </span>
            <h3 className="text-sm font-semibold text-slate-100">eRecept</h3>
          </div>
          {scenario && <span className="text-[11px] text-slate-500">{scenario.prescriber}</span>}
        </div>

        <div className="p-5">
          {scenario && (
            <p className="mb-3 text-[11px] text-slate-500">
              Scenár: <span className="text-slate-300">{scenario.label}</span> — text receptu môžete
              ľubovoľne upraviť.
            </p>
          )}

          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={Math.max(5, text.split("\n").length + 1)}
            spellCheck={false}
            placeholder={"NÁZOV PRÍPRAVKU 500 mg tbl   1-0-1\nĎALŠÍ LIEK 20 mg            1-0-0"}
            className="w-full rounded-lg bg-slate-900 border border-slate-800 focus:border-cyan-700 focus:outline-none text-slate-200 font-mono text-xs leading-relaxed p-3.5 resize-y"
          />

          <p className="mt-3 text-[11px] text-slate-600">
            Podporované zápisy dávkovania: <code className="text-slate-500">1-0-1</code>,{" "}
            <code className="text-slate-500">2x denne</code>, <code className="text-slate-500">1/2-0-0</code>
          </p>
        </div>
      </div>

      <IntakeInterview
        cardId={identity?.patient?.card_id}
        value={intakeAnswers}
        onChange={setIntakeAnswers}
        disabled={!identity}
      />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-[11px] text-slate-500">
          {!identityOk && identity && (
            <span className="text-red-400">
              Totožnosť nebola potvrdená — kontrola prebehne, ale výdaj bude zablokovaný.
            </span>
          )}
        </div>
        <button
          onClick={handleVerify}
          disabled={loading || !text.trim() || !identity}
          className="rounded-lg bg-cyan-500 hover:bg-cyan-400 disabled:bg-slate-800 disabled:text-slate-600 text-slate-950 font-semibold text-sm px-7 py-3 transition-colors flex items-center gap-2"
        >
          {loading ? (
            <>
              <span className="w-3.5 h-3.5 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
              Kontrolujem…
            </>
          ) : (
            <>Spustiť kontrolu výdaja</>
          )}
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-900 bg-red-950/60 px-3 py-2 text-xs text-red-300">
          {error}
        </div>
      )}
    </div>
  );
}

function Header() {
  return (
    <div className="rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900 to-slate-950 px-5 py-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-slate-100">Výdajové okno</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Overenie totožnosti, receptu, interakcií a dávkovania v jednom priechode
          </p>
        </div>
        <div className="flex items-center gap-2 text-[10px]">
          <span className="rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-900 px-2.5 py-1">
            Klinický engine — živé dáta
          </span>
          <span className="rounded-full bg-slate-800 text-slate-400 border border-slate-700 px-2.5 py-1">
            Identita — simulovaná
          </span>
        </div>
      </div>
    </div>
  );
}
