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
  const [screenTick, setScreenTick] = useState(0);
  const pending = useRef(null);
  const identityControls = useRef(null);
  const outcomeControls = useRef(null);
  const voice = useVoiceAgent();

  // The agent's tools are registered once at connect time but must see current
  // state, so everything they read goes through this ref.
  const live = useRef({});

  const scenario = scenarios.find((s) => s.id === scenarioId) ?? null;

  live.current = { phase, identity, groups, groupIndex, answers, scenario, result };

  // The tools are registered once at connect time, so they must never close over
  // render-scoped functions — that is exactly how zapis_odpoved ended up calling a
  // startCheck that still saw identity as null.
  const handlers = useRef({});

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
  }, [voice]);

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

  /**
   * Voice mode only chooses the mode. The agent is not connected yet: it joins after
   * the card and the face, once the kiosk knows who is standing there — so it greets
   * the patient by name and starts at the one question, instead of guessing at a
   * screen it has never seen and making the patient narrate it.
   */
  function startVoice() {
    setMode("voice");
    setPhase("identity");
  }

  /** The agent joins with the verified patient and the actual prescription. */
  function startAgent(id) {
    const preview = scenario?.preview ?? [];
    voice.start({
      clientTools,
      patientName: id?.patient?.name,
      medicines: preview.map((i) => i.trade_name).join(", "),
      schedule: preview.map((i) => `${i.trade_name}: ${i.schedule}`).join("; "),
    });
  }

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

  /**
   * What the agent may read and do.
   *
   * The last transcript failed because the agent had a snapshot taken before the card
   * was even read, so it invented a script and ran ahead of the screen. These read the
   * live state instead, and drive the same actions the buttons do.
   */
  /** The single source of truth about what the patient is looking at. */
  const describeScreen = useCallback(() => {
    const s = live.current;
    const identityStage = identityControls.current;
    const group = s.groups?.[s.groupIndex];

    const step =
      s.phase === "welcome"
        ? "uvod"
        : s.phase === "identity"
        ? identityStage?.stage === "face" || identityStage?.stage === "scanning"
          ? "tvar"
          : "karta"
        : { questions: "otazka", review: "recept", result: "vysledok" }[s.phase] ?? s.phase;

    const state = {
      krok: step,
      meno: s.identity?.patient?.name ?? identityStage?.patientName ?? null,
    };
    if (s.phase === "identity" && identityStage?.busy) {
      state.cakaj = "Prebieha načítanie, počkaj a nepýtaj sa znova.";
    }

    if (step === "otazka" && group) {
      state.otazka = group.questions[0]?.short ?? group.questions[0]?.prompt;
      state.moznosti = group.questions.flatMap((q) => q.options.map((o) => o.label));
    }
    if (s.scenario) {
      state.recept = (s.scenario.preview ?? []).map((i) => `${i.trade_name} — ${i.schedule}`);
    }
    if (s.result) {
      state.vysledok = s.result.verdict_label;
      state.priehradka = s.result.compartment ?? null;
      const o = outcomeControls.current;
      if (o) state.karta_vysledku = o.last ? "posledna — priehradka a QR" : `${o.page + 1} z ${o.pages}`;
      state.rozpis = (s.result.dosing_plan ?? []).map(
        (e) => `${e.trade_name}: ${e.schedule}${e.when ? " " + e.when : ""}`
      );
      state.zistenia = (s.result.next_steps ?? [])
        .flatMap((x) => x.script ?? [])
        .filter((l) => l.patient_visible)
        .map((l) => l.patient);
    }
    return JSON.stringify(state);
  }, []);

  const clientTools = useMemo(
    () => ({
      stav_obrazovky: async () => describeScreen(),


      pokracuj: async () => {
        const before = describeScreen();
        const { moved, note } = handlers.current.advance();
        if (!moved) return `${note} Aktuálny stav: ${before}`;
        // Card read and face scan are asynchronous, so wait for the screen to actually
        // change — but the agent's tool call times out at 5 s, so stop well before that
        // rather than hand back a timeout the agent treats as failure.
        for (let i = 0; i < 17; i++) {
          await new Promise((r) => setTimeout(r, 200));
          const now = describeScreen();
          if (now !== before && !JSON.parse(now).cakaj) return `${note} Aktuálny stav: ${now}`;
        }
        return `${note} Aktuálny stav: ${describeScreen()}`;
      },

      zapis_odpoved: async ({ lieky }) => {
        const note = handlers.current.record(lieky);
        await new Promise((r) => setTimeout(r, 250));
        return `${note} Aktuálny stav: ${describeScreen()}`;
      },
    }),
    [describeScreen]
  );

  // Rebuilt every render, so the tools always act on current state.
  handlers.current = {
    advance: () => {
      if (phase === "welcome") { setPhase("identity"); return { moved: true, note: "Posunuté na ďalší krok." }; }
      if (phase === "identity") { identityControls.current?.next?.(); return { moved: true, note: "Posunuté na ďalší krok." }; }
      if (phase === "questions") {
        // This is how the question got skipped: a patient who tapped through identity
        // himself, then an agent calling pokracuj on the question screen. The question
        // is answered only through zapis_odpoved, never stepped over.
        return { moved: false, note: "Pacient je na otázke. Nepoužívaj pokracuj — opýtaj sa ho a odpoveď zapíš cez zapis_odpoved (prázdny reťazec, ak nič neužíva)." };
      }
      if (phase === "review") { showResult(); return { moved: true, note: "Posunuté na ďalší krok." }; }
      if (phase === "result") {
        const o = outcomeControls.current;
        if (o && !o.last) { o.next(); return { moved: true, note: "Posunuté na ďalšiu kartu výsledku." }; }
        return { moved: false, note: "Pacient je na poslednej obrazovke — vidí priehradku a QR kód. Rozlúč sa a ukonči hovor cez end_call." };
      }
      return { moved: false, note: "Ďalej to nejde." };
    },

    record: (lieky) => {
      const group = groups[groupIndex];
      if (!group) return "Pacient práve nie je na otázke, nedá sa nič zapísať.";

      // The patient speaks freely — "omega tri mastné kyseliny" has to find the option
      // labelled "Rybí olej, omega-3". Whole-phrase matching never would.
      const spoken = String(lieky || "")
        .split(/[;,]/)
        .map((x) => x.trim().toLowerCase())
        .filter(Boolean);
      // "Vitamín D" must not match the option "Vitamín K" — the letter is the whole
      // distinction, and K interacts with warfarin where D does not. So the letter is
      // folded into the token before anything is compared.
      const words = (text) =>
        text
          .toLowerCase()
          .replace(/vitam[ií]n\s+([a-k])\b/g, "vitamin$1")
          .split(/[^a-záäčďéíĺľňóôŕšťúýž0-9]+/)
          .filter((w) => w.length > 2);

      const merged = { ...answers };
      const matchedLabels = [];
      const usedPhrases = new Set();

      for (const q of group.questions) {
        const picked = [];
        for (const option of q.options) {
          if (option.exclusive) continue;
          const optionWords = words(option.label);
          const hit = spoken.find((phrase) =>
            words(phrase).some((w) => optionWords.some((ow) => ow.includes(w) || w.includes(ow)))
          );
          if (hit) {
            picked.push(option.id);
            matchedLabels.push(option.label);
            usedPhrases.add(hit);
          }
        }
        const none = q.options.find((o) => o.exclusive);
        merged[q.id] = picked.length ? picked : none ? [none.id] : [];
      }

      setAnswers(merged);
      startCheck(merged);
      setPhase("review");

      // The agent sends option labels verbatim, and labels contain commas — so the
      // split above turns "Rybí olej, omega-3" into two phrases. A phrase counts as
      // understood if any option on the screen covers it, not only the one that was
      // credited with the match.
      const allOptionWords = group.questions.flatMap((q) => q.options.map((o) => words(o.label)));
      const unmatched = spoken.filter(
        (p) =>
          !usedPhrases.has(p) &&
          !allOptionWords.some((ow) => words(p).some((w) => ow.some((x) => x.includes(w) || w.includes(x))))
      );
      if (!spoken.length) return "Zapísané, že pacient neužíva nič okrem receptu. Teraz je na kroku recept.";
      let msg = matchedLabels.length
        ? `Zapísané: ${matchedLabels.join(", ")}.`
        : "Nič z povedaného nezodpovedá možnostiam na obrazovke.";
      if (unmatched.length) {
        msg += ` Toto v zozname nemám: ${unmatched.join(", ")} — povedz pacientovi, že to odovzdáš obsluhe lekárne.`;
      }
      return msg + " Teraz je pacient na kroku recept.";
    },
  };

  // The agent must never depend on the patient telling it what the screen shows.
  // Every change of step is pushed to it the moment it happens — including the ones
  // the patient makes by tapping while the agent is still talking.
  const voiceLive = voice.status === "live";
  const voiceSay = voice.say;
  useEffect(() => {
    if (!voiceLive) return;
    voiceSay(`Obrazovka sa práve zmenila. Aktuálny stav: ${describeScreen()}`);
  }, [voiceLive, voiceSay, describeScreen, phase, groupIndex, result, screenTick]);

  // Dev only: the agent drives the kiosk through these, and a browser pane cannot
  // grant a microphone — so exposing them is the only way to exercise the voice path
  // end to end instead of shipping it untested.
  useEffect(() => {
    if (!import.meta.env.DEV) return;
    window.__kioskTools = clientTools;
    return () => delete window.__kioskTools;
  }, [clientTools]);

  const stepIndex = useMemo(
    () => ({ welcome: 0, identity: 1, questions: 2, review: 3, result: 4 }[phase] ?? 0),
    [phase]
  );

  return (
    <div className="mx-auto max-w-2xl">
      {/* Demo control, deliberately outside the patient flow. */}
      <div className="mb-3 rounded-card border border-dashed border-hairline px-4 py-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[10px] font-mono uppercase tracking-[0.14em] text-txt3 mr-1">
            Demo — situácia
          </span>
          {scenarios.map((sc) => (
            <button
              key={sc.id}
              onClick={() => {
                setScenarioId(sc.id);
                restart();
              }}
              className={`rounded-sm2 border px-2.5 py-1 text-xs transition ${
                sc.id === scenarioId
                  ? "border-brand bg-brand/10 text-brand"
                  : "border-hairline text-txt3 hover:border-hairline2 hover:text-txt2"
              }`}
            >
              {sc.label}
            </button>
          ))}
        </div>
      </div>

      <div className="rounded-card border border-hairline bg-ink overflow-hidden shadow-2xl">
        <VoiceBar
          status={voice.status}
          speaking={voice.speaking}
          muted={voice.muted}
          level={voice.level}
          onToggleMute={voice.toggleMute}
          onRetry={() => startAgent(identity)}
        />

        {/* Where am I, how much is left */}
        <div className="flex items-center gap-3 px-6 sm:px-10 pt-5">
          {STEPS.map((label, i) => (
            <div key={label} className="flex-1">
              <span
                className={`block h-1 rounded-full transition-colors duration-300 ${
                  i < stepIndex ? "bg-brand" : i === stepIndex ? "bg-brand" : "bg-surface2"
                }`}
              />
              <span
                className={`mt-1.5 block text-[10px] ${
                  i === stepIndex ? "text-brand" : "text-txt3"
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
                    className="w-full rounded-pill border border-hairline2 text-txt2 text-lg py-4 hover:border-white/30 hover:text-txt active:scale-[0.99] transition"
                  >
                    Budem klikať sám
                  </button>
                  {!voice.available && (
                    <p className="text-center text-[11px] text-txt3">
                      Hlasový sprievodca práve nie je dostupný.
                    </p>
                  )}
                </div>
              }
            >
              <div className="text-center">
                <div className="w-16 h-16 rounded-card bg-brand grid place-items-center mx-auto mb-7">
                  <svg className="w-8 h-8 text-ink" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.6-4A12 12 0 0112 2.9 12 12 0 013.4 6 12 12 0 003 9c0 5.6 3.8 10.3 9 11.6 5.2-1.3 9-6 9-11.6 0-1-.1-2-.4-3z" />
                  </svg>
                </div>
                <Title sub="Hlasom sa nemusíte dotknúť obrazovky. Alebo si všetko odkliknete sami. Obe cesty trvajú asi minútu a pol.">
                  Dobrý deň
                </Title>
              </div>
            </Screen>
          )}

          {phase === "identity" && (
            <KioskIdentity
              controls={identityControls}
              auto={mode === "voice"}
              onDone={(id) => {
                setIdentity(id);
                setPhase("questions");
                if (mode === "voice") startAgent(id);
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
                  {error && <p className="text-sm text-bad text-center">{error}</p>}
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
                      className="rounded-card border border-hairline bg-surface px-4 py-3.5"
                    >
                      <p className="text-txt text-base font-medium leading-tight">
                        {item.trade_name}
                        {item.strength && (
                          <span className="text-txt3 font-normal"> · {item.strength}</span>
                        )}
                      </p>
                      <p className="text-brand text-sm mt-0.5">{item.schedule}</p>
                    </li>
                  ))}
                </ul>
              </div>
            </Screen>
          )}

          {phase === "result" && result && (
            <KioskOutcome
              data={result}
              onRestart={restart}
              controls={outcomeControls}
              onPageChange={() => setScreenTick((t) => t + 1)}
            />
          )}
        </div>
      </div>

      <p className="mt-4 text-center text-[11px] text-txt3">
        Rovnaký klinický engine ako pultová konzola · identita a eRecept sú v deme simulované
      </p>
    </div>
  );
}
