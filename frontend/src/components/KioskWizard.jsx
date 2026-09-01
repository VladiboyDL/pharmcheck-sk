import { useEffect, useRef, useState } from "react";
import KioskIdentity from "./kiosk/KioskIdentity";
import KioskOutcome from "./kiosk/KioskOutcome";
import { Screen, Title, BigButton, Rail } from "./kiosk/KioskShell";
import { getIntakeQuestions, getScenario, verifyDispense } from "../api/client";

/**
 * The patient-facing side of the same engine the pharmacist console runs on.
 *
 * One decision per screen. The prescription loads in the background while the
 * questions are being asked, so the wait never has a spinner in front of it.
 */
export default function KioskWizard({ onSessionResult }) {
  const [phase, setPhase] = useState("welcome"); // welcome|identity|greet|questions|review|checking|result
  const [identity, setIdentity] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [qIndex, setQIndex] = useState(0);
  const [scenario, setScenario] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const answersRef = useRef({});

  // Prescription and questions are fetched the moment identity is known, so the
  // patient is answering questions while the network work already happened.
  useEffect(() => {
    const cardId = identity?.patient?.card_id;
    if (!cardId) return;
    getScenario(cardId).then(setScenario).catch(() => {});
    getIntakeQuestions(cardId)
      .then((d) => setQuestions(d.questions))
      .catch(() => setQuestions([]));
  }, [identity?.patient?.card_id]);

  useEffect(() => {
    if (phase !== "greet") return;
    const t = setTimeout(() => setPhase("questions"), 2200);
    return () => clearTimeout(t);
  }, [phase]);

  async function runCheck() {
    setPhase("checking");
    setError(null);
    try {
      const [data] = await Promise.all([
        verifyDispense({
          cardId: identity.patient.card_id,
          prescriptionText: scenario?.text ?? "",
          identityVerified: identity.biometric?.verified === true,
          intake: answersRef.current,
        }),
        // A verdict in 8 ms reads as "it did not look". Give the reassurance a beat.
        new Promise((r) => setTimeout(r, 2100)),
      ]);
      setResult(data);
      onSessionResult?.(data);
      setPhase("result");
    } catch (e) {
      setError(e.message);
      setPhase("review");
    }
  }

  function answer(question, optionId) {
    const current = answers[question.id] || [];
    const option = question.options.find((o) => o.id === optionId);
    let next;
    if (!question.multi || option?.exclusive) {
      next = [optionId];
    } else {
      const withoutExclusive = current.filter(
        (id) => !question.options.find((o) => o.id === id)?.exclusive
      );
      next = withoutExclusive.includes(optionId)
        ? withoutExclusive.filter((id) => id !== optionId)
        : [...withoutExclusive, optionId];
    }
    const merged = { ...answers, [question.id]: next };
    setAnswers(merged);
    answersRef.current = merged;
    // Single-choice questions advance on their own — no second tap to confirm.
    if (!question.multi) setTimeout(() => advanceQuestion(), 260);
  }

  function advanceQuestion() {
    setQIndex((i) => {
      if (i + 1 >= questions.length) {
        setPhase("review");
        return i;
      }
      return i + 1;
    });
  }

  function restart() {
    setPhase("welcome");
    setIdentity(null);
    setQuestions([]);
    setAnswers({});
    answersRef.current = {};
    setQIndex(0);
    setScenario(null);
    setResult(null);
    setError(null);
  }

  return (
    <div className="mx-auto max-w-2xl">
      <div className="rounded-3xl border border-slate-800 bg-slate-950 px-6 sm:px-10 py-8 shadow-2xl">
        {phase === "welcome" && (
          <Screen footer={<BigButton onClick={() => setPhase("identity")} full>Začať</BigButton>}>
            <div className="text-center">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-400 to-blue-600 grid place-items-center mx-auto mb-7">
                <svg className="w-8 h-8 text-slate-950" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.6-4A12 12 0 0112 2.9 12 12 0 013.4 6 12 12 0 003 9c0 5.6 3.8 10.3 9 11.6 5.2-1.3 9-6 9-11.6 0-1-.1-2-.4-3z" />
                </svg>
              </div>
              <Title sub="Skontrolujeme váš recept a bezpečnosť liekov, ktoré užívate. Trvá to necelé dve minúty.">
                Dobrý deň
              </Title>
            </div>
          </Screen>
        )}

        {phase === "identity" && (
          <KioskIdentity
            onDone={(id) => {
              setIdentity(id);
              setPhase("greet");
            }}
          />
        )}

        {phase === "greet" && (
          <Screen>
            <div className="text-center">
              <Title sub="Sťahujem váš recept z eZdravia. Medzitým sa vás opýtam na pár vecí.">
                Vitajte, {identity.patient.name.split(" ")[0]}
              </Title>
              <div className="mt-9 flex justify-center gap-1.5">
                {[0, 1, 2].map((i) => (
                  <span
                    key={i}
                    className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce"
                    style={{ animationDelay: `${i * 140}ms` }}
                  />
                ))}
              </div>
            </div>
          </Screen>
        )}

        {phase === "questions" && questions.length > 0 && (
          <QuestionScreen
            question={questions[qIndex]}
            index={qIndex}
            total={questions.length}
            chosen={answers[questions[qIndex].id] || []}
            onPick={(id) => answer(questions[qIndex], id)}
            onNext={advanceQuestion}
          />
        )}

        {phase === "review" && (
          <Screen
            footer={
              <div className="space-y-4">
                <BigButton onClick={runCheck} full>
                  Skontrolovať
                </BigButton>
                {error && <p className="text-sm text-red-400 text-center">{error}</p>}
              </div>
            }
          >
            <div>
              <Title sub="Toto vám predpísal lekár. Skontrolujeme to spolu s tým, čo ste mi povedali.">
                Váš recept
              </Title>
              <ul className="mt-8 space-y-2">
                {(scenario?.text ?? "").split("\n").filter(Boolean).map((line, n) => (
                  <li
                    key={n}
                    className="rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-3 text-slate-200 font-mono text-sm"
                  >
                    {line.trim()}
                  </li>
                ))}
              </ul>
              {scenario?.prescriber && (
                <p className="mt-4 text-center text-xs text-slate-500">{scenario.prescriber}</p>
              )}
            </div>
          </Screen>
        )}

        {phase === "checking" && <CheckingScreen />}

        {phase === "result" && result && <KioskOutcome data={result} onRestart={restart} />}
      </div>

      <p className="mt-4 text-center text-[11px] text-slate-600">
        Rovnaký klinický engine ako pultová konzola · identita a eRecept sú v deme simulované
      </p>
    </div>
  );
}

function QuestionScreen({ question, index, total, chosen, onPick, onNext }) {
  const hasAnswer = chosen.length > 0;
  return (
    <Screen
      footer={
        <div className="space-y-4">
          {question.multi && (
            <BigButton onClick={onNext} full tone={hasAnswer ? "primary" : "ghost"}>
              {hasAnswer ? "Pokračovať" : "Preskočiť"}
            </BigButton>
          )}
          <Rail steps={total} current={index} />
        </div>
      }
    >
      <div>
        <p className="text-center text-xs uppercase tracking-wider text-slate-500 mb-4">
          Otázka {index + 1} z {total}
        </p>
        <Title sub={question.hint}>{question.prompt}</Title>

        <div className="mt-8 grid gap-2.5">
          {question.options.map((o) => {
            const active = chosen.includes(o.id);
            return (
              <button
                key={o.id}
                onClick={() => onPick(o.id)}
                aria-pressed={active}
                className={`w-full rounded-2xl border-2 px-5 py-4 text-left text-lg transition-colors ${
                  active
                    ? o.exclusive
                      ? "border-slate-500 bg-slate-800 text-slate-100"
                      : "border-amber-500 bg-amber-950/40 text-amber-100"
                    : "border-slate-800 bg-slate-900/50 text-slate-300 hover:border-slate-600"
                }`}
              >
                <span className="flex items-center gap-3">
                  <span
                    className={`w-5 h-5 rounded-md border-2 grid place-items-center flex-shrink-0 ${
                      active ? "border-current" : "border-slate-700"
                    }`}
                  >
                    {active && (
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </span>
                  {o.label}
                </span>
              </button>
            );
          })}
        </div>

        {question.multi && (
          <p className="mt-4 text-center text-xs text-slate-600">Môžete označiť aj viac možností</p>
        )}
      </div>
    </Screen>
  );
}

const CHECK_STEPS = [
  "Kontrolujem liekové interakcie",
  "Overujem dávkovanie podľa vašich obličiek",
  "Hľadám duplicitnú liečbu",
  "Pripravujem odporúčanie",
];

function CheckingScreen() {
  const [step, setStep] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setStep((s) => Math.min(s + 1, CHECK_STEPS.length - 1)), 520);
    return () => clearInterval(t);
  }, []);
  return (
    <Screen>
      <div className="text-center">
        <div className="w-16 h-16 mx-auto mb-8 rounded-full border-4 border-slate-800 border-t-cyan-400 animate-spin" />
        <Title>Kontrolujem</Title>
        <ul className="mt-8 space-y-2 max-w-sm mx-auto text-left">
          {CHECK_STEPS.map((label, i) => (
            <li
              key={label}
              className={`flex items-center gap-3 text-sm transition-opacity ${
                i <= step ? "opacity-100" : "opacity-30"
              }`}
            >
              <span
                className={`w-4 h-4 rounded-full grid place-items-center flex-shrink-0 ${
                  i < step ? "bg-emerald-500" : i === step ? "bg-cyan-400 animate-pulse" : "bg-slate-800"
                }`}
              >
                {i < step && (
                  <svg className="w-2.5 h-2.5 text-slate-950" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                )}
              </span>
              <span className="text-slate-300">{label}</span>
            </li>
          ))}
        </ul>
      </div>
    </Screen>
  );
}
