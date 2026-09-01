import { useEffect, useState } from "react";
import IdentityGate from "./IdentityGate";
import IntakeInterview from "./IntakeInterview";
import DispenseResult from "./DispenseResult";
import { getScenarios, verifyDispense } from "../api/client";

/**
 * The dispensing window: identity → prescription → verification decision.
 * This is the flow that replaces the manual counter check.
 */
export default function DispensingWindow({ onSessionResult }) {
  const [identity, setIdentity] = useState(null);
  const [scenarios, setScenarios] = useState([]);
  const [scenarioId, setScenarioId] = useState(null);
  const [text, setText] = useState("");
  const [intakeAnswers, setIntakeAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const identityOk = identity?.biometric?.verified === true;

  useEffect(() => {
    getScenarios()
      .then((d) => {
        setScenarios(d.scenarios);
        if (!scenarioId && d.scenarios[0]) {
          setScenarioId(d.scenarios[0].id);
          setText(d.scenarios[0].text);
        }
      })
      .catch(() => {});
  }, []);

  const scenario = scenarios.find((s) => s.id === scenarioId) ?? null;

  function pickScenario(sc) {
    setScenarioId(sc.id);
    setText(sc.text);
    setIntakeAnswers(sc.suggested_intake ?? {});
  }

  async function handleVerify() {
    setLoading(true);
    setError(null);
    try {
      const data = await verifyDispense({
        cardId: identity.patient.card_id,
        prescriptionText: text,
        identityVerified: identityOk,
        intake: intakeAnswers,
        scenario: scenarioId,
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
    setText(scenarios[0]?.text ?? "");
    setScenarioId(scenarios[0]?.id ?? null);
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
        className={`rounded-card border bg-ink overflow-hidden transition-opacity ${
          identity ? "border-hairline opacity-100" : "border-hairline opacity-40 pointer-events-none"
        }`}
      >
        <div className="flex items-center justify-between px-5 py-3 border-b border-hairline bg-surface">
          <div className="flex items-center gap-2.5">
            <span className="w-6 h-6 rounded-md bg-brand/15 text-brand grid place-items-center text-[11px] font-bold">
              2
            </span>
            <h3 className="text-sm font-semibold text-txt">eRecept</h3>
          </div>
          {scenario && <span className="text-[11px] text-txt3">{scenario.prescriber}</span>}
        </div>

        <div className="p-5">
          <div className="mb-4">
            <p className="text-[10px] font-mono uppercase tracking-[0.14em] text-txt3 mb-2">
              Demo — klinická situácia toho istého pacienta
            </p>
            <div className="flex flex-wrap gap-1.5">
              {scenarios.map((sc) => (
                <button
                  key={sc.id}
                  onClick={() => pickScenario(sc)}
                  className={`rounded-sm2 border px-2.5 py-1.5 text-xs transition-colors ${
                    sc.id === scenarioId
                      ? "border-brand bg-brand/10 text-brand"
                      : "border-hairline bg-surface text-txt2 hover:border-hairline2"
                  }`}
                >
                  {sc.label}
                </button>
              ))}
            </div>
            {scenario && (
              <p className="mt-2 text-[11px] text-txt3">
                {scenario.subtitle} — text receptu môžete ľubovoľne upraviť.
              </p>
            )}
          </div>

          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={Math.max(5, text.split("\n").length + 1)}
            spellCheck={false}
            placeholder={"NÁZOV PRÍPRAVKU 500 mg tbl   1-0-1\nĎALŠÍ LIEK 20 mg            1-0-0"}
            className="w-full rounded-sm2 bg-panel border border-hairline focus:border-brand focus:outline-none text-txt font-mono text-xs leading-relaxed p-3.5 resize-y"
          />

          <p className="mt-3 text-[11px] text-txt3">
            Podporované zápisy dávkovania: <code className="text-txt3">1-0-1</code>,{" "}
            <code className="text-txt3">2x denne</code>, <code className="text-txt3">1/2-0-0</code>
          </p>
        </div>
      </div>

      <IntakeInterview
        cardId={identity?.patient?.card_id}
        scenarioId={scenarioId}
        value={intakeAnswers}
        onChange={setIntakeAnswers}
        disabled={!identity}
      />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-[11px] text-txt3">
          {!identityOk && identity && (
            <span className="text-bad">
              Totožnosť nebola potvrdená — kontrola prebehne, ale výdaj bude zablokovaný.
            </span>
          )}
        </div>
        <button
          onClick={handleVerify}
          disabled={loading || !text.trim() || !identity}
          className="rounded-sm2 bg-brand hover:bg-brand disabled:bg-surface2 disabled:text-txt3 text-slate-950 font-semibold text-sm px-7 py-3 transition-colors flex items-center gap-2"
        >
          {loading ? (
            <>
              <span className="w-3.5 h-3.5 border-2 border-hairline border-t-transparent rounded-full animate-spin" />
              Kontrolujem…
            </>
          ) : (
            <>Spustiť kontrolu výdaja</>
          )}
        </button>
      </div>

      {error && (
        <div className="rounded-sm2 border border-bad/40 bg-bad/10 px-3 py-2 text-xs text-bad">
          {error}
        </div>
      )}
    </div>
  );
}

function Header() {
  return (
    <div className="rounded-card border border-hairline bg-brand/15 px-5 py-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-txt">Výdajové okno</h2>
          <p className="text-xs text-txt3 mt-0.5">
            Overenie totožnosti, receptu, interakcií a dávkovania v jednom priechode
          </p>
        </div>
        <div className="flex items-center gap-2 text-[10px]">
          <span className="rounded-full bg-ok/10 text-ok border border-ok/40 px-2.5 py-1">
            Klinický engine — živé dáta
          </span>
          <span className="rounded-full bg-surface2 text-txt2 border border-hairline2 px-2.5 py-1">
            Identita — simulovaná
          </span>
        </div>
      </div>
    </div>
  );
}
