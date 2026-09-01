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
  const [mode, setMode] = useState(null); // null | "voice" | "tap"
  const pending = useRef(null);
  const identityControls = useRef(null);
  const voice = useVoiceAgent();

  // The agent's tools are registered once at connect time but must see current
  // state, so everything they read goes through this ref.
  const live = useRef({});

  const scenario = scenarios.find((s) => s.id === scenarioId) ?? null;

  live.current = { phase, identity, groups, groupIndex, answers, scenario, result };

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
    setMode(null);
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
  function startVoice() {
    setMode("voice");
    setPhase("identity");
    voice.start({ clientTools });
  }

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

  // Voice mode is announced once; from then on the agent reads the screen through
  // stav_obrazovky rather than being pushed narration it might get ahead of.
  useEffect(() => {
    if (mode !== "voice" || voice.status !== "live") return;
    voice.say(`Pacient je na kroku ${phase}.`);
  }, [phase, mode, voice.status]);

  /**
   * What the agent may read and do.
   *
   * The last transcript failed because the agent had a snapshot taken before the card
   * was even read, so it invented a script and ran ahead of the screen. These read the
   * live state instead, and drive the same actions the buttons do.
   */
  const clientTools = useMemo(
    () => ({
      stav_obrazovky: async () => {
        const s = live.current;
        const group = s.groups?.[s.groupIndex];
        const state = {
          krok: {
            welcome: "uvod",
            identity: identityControls.current?.stage === "face" ? "tvar" : "karta",
            questions: "otazka",
            review: "recept",
            result: "vysledok",
          }[s.phase] ?? s.phase,
          meno: s.identity?.patient?.name ?? null,
        };

        if (state.krok === "otazka" && group) {
          state.otazka = group.questions[0]?.short ?? group.questions[0]?.prompt;
          state.moznosti = group.questions.flatMap((q) => q.options.map((o) => o.label));
        }
        if (s.scenario) {
          state.recept = (s.scenario.preview ?? []).map(
            (i) => `${i.trade_name} — ${i.schedule}`
          );
        }
        if (s.result) {
          state.vysledok = s.result.verdict_label;
          state.rozpis = (s.result.dosing_plan ?? []).map(
            (e) => `${e.trade_name}: ${e.schedule}${e.when ? " " + e.when : ""}`
          );
          state.zistenia = (s.result.next_steps ?? [])
            .flatMap((x) => x.script ?? [])
            .filter((l) => l.patient_visible)
            .map((l) => l.patient);
        }
        return JSON.stringify(state);
      },

      pokracuj: async () => {
        const s = live.current;
        if (s.phase === "welcome") setPhase("identity");
        else if (s.phase === "identity") identityControls.current?.next?.();
        else if (s.phase === "questions") nextGroup();
        else if (s.phase === "review") await showResult();
        else if (s.phase === "result") return "Pacient je na poslednej obrazovke.";
        return "Posunuté.";
      },

      zapis_odpoved: async ({ lieky }) => {
        const s = live.current;
        const group = s.groups?.[s.groupIndex];
        if (!group) return "Momentálne nie sme na otázke.";

        const wanted = String(lieky || "")
          .split(";")
          .map((x) => x.trim().toLowerCase())
          .filter(Boolean);

        const merged = { ...s.answers };
        for (const q of group.questions) {
          const picked = q.options
            .filter((o) => !o.exclusive && wanted.some((w) => o.label.toLowerCase().includes(w)))
            .map((o) => o.id);
          const none = q.options.find((o) => o.exclusive);
          merged[q.id] = picked.length ? picked : none ? [none.id] : [];
        }
        setAnswers(merged);
        startCheck(merged);
        setPhase("review");
        return wanted.length ? `Zapísané: ${wanted.join(", ")}.` : "Zapísané, že neužíva nič iné.";
      },
    }),
    []
  );

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
                <div className="space-y-3">
                  <BigButton onClick={startVoice} disabled={!voice.available} full>
                    Preveďte ma hlasom
                  </BigButton>
                  <button
                    onClick={() => {
                      setMode("tap");
                      setPhase("identity");
                    }}
                    className="w-full rounded-2xl border border-slate-700 text-slate-300 text-lg py-4 hover:border-slate-500 active:scale-[0.99] transition"
                  >
                    Budem klikať sám
                  </button>
                  {!voice.available && (
                    <p className="text-center text-[11px] text-slate-600">
                      Hlasový sprievodca práve nie je dostupný.
                    </p>
                  )}
                </div>
              }
            >
              <div className="text-center">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-400 to-blue-600 grid place-items-center mx-auto mb-7">
                  <svg className="w-8 h-8 text-slate-950" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.6-4A12 12 0 0112 2.9 12 12 0 013.4 6 12 12 0 003 9c0 5.6 3.8 10.3 9 11.6 5.2-1.3 9-6 9-11.6 0-1-.1-2-.4-3z" />
                  </svg>
                </div>
                <Title sub="Môžem vás previesť hlasom, alebo si všetko odkliknete sami. Obe cesty trvajú asi minútu a pol.">
                  Dobrý deň
                </Title>
              </div>
            </Screen>
          )}

          {phase === "identity" && (
            <KioskIdentity
              controls={identityControls}
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
