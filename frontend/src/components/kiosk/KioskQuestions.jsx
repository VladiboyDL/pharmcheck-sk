import { Screen, Title, BigButton } from "./KioskShell";
import KioskIcon from "./KioskIcon";

/**
 * One screen per group of related questions, not one per question.
 *
 * Five screens of a single question each is a form. The common answer is "nothing",
 * so that escape is the largest target on the screen and ends the group in one tap.
 */
export default function KioskQuestions({ group, greeting, answers, onChange, onNext, onBack }) {
  const questions = group.questions;

  function toggle(question, optionId) {
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
    onChange({ ...answers, [question.id]: next });
  }

  /** "Nothing at all" answers every question on the screen and moves on. */
  function nothingHere() {
    const merged = { ...answers };
    for (const q of questions) {
      const none = q.options.find((o) => o.exclusive) || q.options[q.options.length - 1];
      merged[q.id] = [none.id];
    }
    onChange(merged);
    setTimeout(onNext, 180);
  }

  const anyPicked = questions.some((q) =>
    (answers[q.id] || []).some((id) => !q.options.find((o) => o.id === id)?.exclusive)
  );

  return (
    <Screen
      footer={
        <div className="space-y-3">
          <BigButton onClick={onNext} full>
            Pokračovať
          </BigButton>
          {!anyPicked && (
            <button
              onClick={nothingHere}
              className="w-full rounded-pill border border-hairline2 text-txt2 text-lg py-4 hover:border-white/30 hover:text-txt active:scale-[0.99] transition"
            >
              Nič iné neberiem
            </button>
          )}
        </div>
      }
    >
      <div>
        {greeting && (
          <p className="text-center text-lg text-txt2 mb-5">
            Vitajte, <span className="text-txt font-semibold">{greeting}</span>.{" "}
            {questions.length === 1 ? "Mám jednu otázku." : `Mám ${questions.length} otázky.`}
          </p>
        )}

        <div className="space-y-7">
          {questions.map((q) => (
            <fieldset key={q.id}>
              <legend className="text-xl sm:text-2xl font-bold text-txt tracking-tight text-balance">
                {q.short || q.prompt}
              </legend>
              <div className="mt-4 grid gap-2.5 sm:grid-cols-2">
                {q.options.map((o) => {
                  const active = (answers[q.id] || []).includes(o.id);
                  return (
                    <button
                      key={o.id}
                      onClick={() => toggle(q, o.id)}
                      aria-pressed={active}
                      className={`flex items-center gap-3 rounded-card border-2 px-4 py-4 text-left text-base transition active:scale-[0.98] ${
                        active
                          ? o.exclusive
                            ? "border-hairline2 bg-surface2 text-txt"
                            : "border-warn/40 bg-warn/10 text-warn"
                          : "border-hairline bg-surface text-txt2 hover:border-hairline2"
                      }`}
                    >
                      <span
                        className={`w-9 h-9 rounded-sm2 grid place-items-center flex-shrink-0 ${
                          active ? "bg-current/10" : "bg-surface2/70"
                        }`}
                      >
                        {o.icon ? (
                          <KioskIcon name={o.icon} className="w-5 h-5" />
                        ) : (
                          <span className={`w-2.5 h-2.5 rounded-full ${active ? "bg-current" : "bg-slate-600"}`} />
                        )}
                      </span>
                      <span className="leading-tight">{o.label}</span>
                    </button>
                  );
                })}
              </div>
            </fieldset>
          ))}
        </div>
      </div>
    </Screen>
  );
}
