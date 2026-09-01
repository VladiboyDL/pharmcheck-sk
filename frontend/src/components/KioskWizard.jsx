import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import KioskIdentity from "./kiosk/KioskIdentity";
import KioskOutcome from "./kiosk/KioskOutcome";
import KioskQuestions from "./kiosk/KioskQuestions";
import { Screen, Title, BigButton } from "./kiosk/KioskShell";
import VoiceBar from "./kiosk/VoiceBar";
import useVoiceAgent from "../hooks/useVoiceAgent";
import { getIntakeQuestions, getScenarios, verifyDispense } from "../api/client";

const STEPS = ["Vitajte", "Totožnosť", "Otázky", "Recept", "Hotovo"];
const IDLE_RESET_MS = 120000;

/**
 * The patient-facing side of the same engine the pharmacist console runs on.
 *
 * Optimised for time-to-medicine: the check starts the moment the last question is
 * answered and runs underneath the prescription screen, so the result is already
 * waiting by the time the patient taps through. Nobody watches a spinner.
 */
export default function KioskWizard({ onSessionResult }) {
  const [phase, setPhase] = useState("welcome"); // welcome|identity|questions|review|result
  const [identity, setIdentity] = useState(null);
  const [groups, setGroups] = useState([]);
  const [groupIndex, setGroupIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [scenarios, setScenarios] = useState([]);
  const [scenarioId, setScenarioId] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const pending = useRef(null);
  const voice = useVoiceAgent();

  const scenario = scenarios.find((s) => s.id === scenarioId) ?? null;

  useEffect(() => {
    getScenarios()
      .then((d) => {
        setScenarios(d.scenarios);
        setScenarioId((id) => id ?? d.scenarios[0]?.id ?? null);
      })
      .catch(() => {});
  }, []);

  // Questions load while the patient is still tapping their card.
  useEffect(() => {
    const cardId = identity?.patient?.card_id;
    if (!cardId) return;
    getIntakeQuestions(cardId, scenarioId)
      .then((d) => {
        const byGroup = [];
        for (const q of d.questions) {
          const existing = byGroup.find((g) => g.id === q.group);
          if (existing) existing.questions.push(q);
          else byGroup.push({ id: q.group, questions: [q] });
        }
        setGroups(byGroup);
      })
      .catch(() => setGroups([]));
  }, [identity?.patient?.card_id, scenarioId]);

  const restart = useCallback(() => {
    voice.stop();
    setPhase("welcome");
    setIdentity(null);
    setGroups([]);
    setGroupIndex(0);
    setAnswers({});
    setResult(null);
    setError(null);
    pending.current = null;
  }, []);

  // A kiosk nobody is standing at must return to the start on its own.
  useEffect(() => {
    if (phase === "welcome") return;
    let timer = setTimeout(restart, IDLE_RESET_MS);
    const bump = () => {
      clearTimeout(timer);
      timer = setTimeout(restart, IDLE_RESET_MS);
    };
    window.addEventListener("pointerdown", bump);
    window.addEventListener("keydown", bump);
    return () => {
      clearTimeout(timer);
      window.removeEventListener("pointerdown", bump);
      window.removeEventListener("keydown", bump);
    };
  }, [phase, restart]);

  /** Fire the check now; the prescription screen covers its latency. */
  function startCheck(finalAnswers) {
    setError(null);
    const request = verifyDispense({
      cardId: identity.patient.card_id,
      prescriptionText: scenario?.text ?? "",
      identityVerified: identity.biometric?.verified === true,
      intake: finalAnswers,
      scenario: scenarioId,
    });
    // The result is awaited a screen later, so swallow the rejection now to avoid an
    // unhandled-rejection warning; showResult still sees it when it awaits.
    request.catch(() => {});
    pending.current = request;
  }

  async function showResult() {
    try {
      const data = await (pending.current ?? Promise.reject(new Error("Kontrola nebola spustená")));
      setResult(data);
      onSessionResult?.(data);
      setPhase("result");
    } catch (e) {
      setError(e.message);
    }
  }

  function nextGroup() {
    if (groupIndex + 1 < groups.length) {
      setGroupIndex((i) => i + 1);
      return;
    }
    startCheck(answers);
    setPhase("review");
  }

  // Voice needs a user gesture to get the microphone, so it starts on "Začať" and
  // then follows the patient through the flow.
  useEffect(() => {
    if (!voice.available || voice.status !== "live") return;
    const lines = {
      identity: "Pacient prikladá kartu poistenca pod čítačku.",
      questions: "Pýtam sa, či okrem receptu užíva ešte niečo.",
      review: "Ukazujem mu recept od lekára.",
    };
    if (lines[phase]) voice.say(lines[phase]);
  }, [phase, voice.available, voice.status]);

  // Once the check is done the agent can talk about the actual medicines.
  useEffect(() => {
    if (!result || voice.status !== "live") return;
    const plan = (result.dosing_plan ?? [])
      .map((e) => `${e.trade_name}: ${e.schedule}${e.when ? " " + e.when : ""}`)
      .join("; ");
    const findings = (result.next_steps ?? [])
      .flatMap((s) => s.script ?? [])
      .filter((l) => l.patient_visible)
      .map((l) => l.patient)
      .join(" ");
    voice.say(
      `Kontrola je hotová. Výsledok: ${result.verdict_label}. ` +
        `Rozpis liekov: ${plan}. ` +
        (findings ? `Na čo upozorniť: ${findings}` : "Žiadne upozornenia.")
    );
  }, [result, voice.status]);

  const stepIndex = useMemo(
    () => ({ welcome: 0, identity: 1, questions: 2, review: 3, result: 4 }[phase] ?? 0),
    [phase]
  );

  return (
    <div className="mx-auto max-w-2xl">
      {/* Demo control, deliberately outside the patient flow. */}
      <div className="mb-3 rounded-2xl border border-dashed border-slate-800 px-4 py-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[10px] uppercase tracking-wider text-slate-600 mr-1">
            Demo — situácia
          </span>
          {scenarios.map((sc) => (
            <button
              key={sc.id}
              onClick={() => {
                setScenarioId(sc.id);
                restart();
              }}
              className={`rounded-lg border px-2.5 py-1 text-xs transition ${
                sc.id === scenarioId
                  ? "border-cyan-700 bg-cyan-950/50 text-cyan-200"
                  : "border-slate-800 text-slate-500 hover:border-slate-600 hover:text-slate-300"
              }`}
            >
              {sc.label}
            </button>
          ))}
        </div>
      </div>

      <div className="rounded-3xl border border-slate-800 bg-slate-950 overflow-hidden shadow-2xl">
        <VoiceBar
          status={voice.status}
          speaking={voice.speaking}
          muted={voice.muted}
          level={voice.level}
          onToggleMute={voice.toggleMute}
          onRetry={() => voice.start({ patientName: identity?.patient?.name })}
        />

        {/* Where am I, how much is left */}
        <div className="flex items-center gap-3 px-6 sm:px-10 pt-5">
          {STEPS.map((label, i) => (
            <div key={label} className="flex-1">
              <span
                className={`block h-1 rounded-full transition-colors duration-300 ${
                  i < stepIndex ? "bg-cyan-600" : i === stepIndex ? "bg-cyan-400" : "bg-slate-800"
                }`}
              />
              <span
                className={`mt-1.5 block text-[10px] ${
                  i === stepIndex ? "text-cyan-300" : "text-slate-700"
                }`}
              >
                {label}
              </span>
            </div>
          ))}
        </div>

        <div className="px-6 sm:px-10 pb-8 pt-2">
          {phase === "welcome" && (
            <Screen
              footer={
                <BigButton
                  onClick={() => {
                    setPhase("identity");
                    if (voice.available) voice.start({ patientName: "pacient" });
                  }}
                  full
                >
                  Začať
                </BigButton>
              }
            >
              <div className="text-center">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-400 to-blue-600 grid place-items-center mx-auto mb-7">
                  <svg className="w-8 h-8 text-slate-950" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.6-4A12 12 0 0112 2.9 12 12 0 013.4 6 12 12 0 003 9c0 5.6 3.8 10.3 9 11.6 5.2-1.3 9-6 9-11.6 0-1-.1-2-.4-3z" />
                  </svg>
                </div>
                <Title sub="Priložíte kartu, odpoviete na jednu otázku a odchádzate s liekmi. Minúta a pol.">
                  Dobrý deň
                </Title>
              </div>
            </Screen>
          )}

          {phase === "identity" && (
            <KioskIdentity
              onDone={(id) => {
                setIdentity(id);
                setPhase("questions");
              }}
            />
          )}

          {phase === "questions" && groups[groupIndex] && (
            <KioskQuestions
              group={groups[groupIndex]}
              greeting={groupIndex === 0 ? identity.patient.name.split(" ")[0] : null}
              answers={answers}
              onChange={setAnswers}
              onNext={nextGroup}
              onBack={groupIndex > 0 ? () => setGroupIndex((i) => i - 1) : null}
            />
          )}

          {phase === "review" && (
            <Screen
              footer={
                <div className="space-y-3">
                  <BigButton onClick={showResult} full>
                    Pokračovať
                  </BigButton>
                  {error && <p className="text-sm text-red-400 text-center">{error}</p>}
                </div>
              }
            >
              <div>
                <Title sub="Toto vám predpísal lekár. Kontrolujeme to spolu s tým, čo ste mi povedali.">
                  Váš recept
                </Title>
                <ul className="mt-7 space-y-2.5">
                  {(scenario?.preview ?? []).map((item) => (
                    <li
                      key={item.trade_name}
                      className="rounded-2xl border border-slate-800 bg-slate-900/60 px-4 py-3.5"
                    >
                      <p className="text-slate-100 text-base font-medium leading-tight">
                        {item.trade_name}
                        {item.strength && (
                          <span className="text-slate-500 font-normal"> · {item.strength}</span>
                        )}
                      </p>
                      <p className="text-cyan-300 text-sm mt-0.5">{item.schedule}</p>
                    </li>
                  ))}
                </ul>
              </div>
            </Screen>
          )}

          {phase === "result" && result && <KioskOutcome data={result} onRestart={restart} />}
        </div>
      </div>

      <p className="mt-4 text-center text-[11px] text-slate-600">
        Rovnaký klinický engine ako pultová konzola · identita a eRecept sú v deme simulované
      </p>
    </div>
  );
}
