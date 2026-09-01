import { useEffect, useState } from "react";
import { getIntakeQuestions } from "../api/client";

/**
 * The questions the prescriber never asked.
 *
 * A prescription describes what one doctor knew about. The harm at the counter comes
 * from what is missing from it — an Ibalgin bought the same morning, ľubovník for
 * low mood, a second specialist's script. Tap answers, no typing.
 */
export default function IntakeInterview({ cardId, scenarioId, value, onChange, disabled }) {
  const [questions, setQuestions] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!cardId) return;
    getIntakeQuestions(cardId, scenarioId)
      .then((d) => setQuestions(d.questions))
      .catch(() => setError("Otázky sa nepodarilo načítať"));
  }, [cardId, scenarioId]);

  function toggle(question, optionId) {
    const current = value[question.id] || [];
    const option = question.options.find((o) => o.id === optionId);
    let next;

    if (!question.multi || option?.exclusive) {
      next = current.includes(optionId) ? [] : [optionId];
    } else {
      const withoutExclusive = current.filter(
        (id) => !question.options.find((o) => o.id === id)?.exclusive
      );
      next = withoutExclusive.includes(optionId)
        ? withoutExclusive.filter((id) => id !== optionId)
        : [...withoutExclusive, optionId];
    }

    onChange({ ...value, [question.id]: next });
  }

  const answered = questions.filter((q) => (value[q.id] || []).length > 0).length;
  const flagged = questions.reduce((n, q) => {
    const chosen = value[q.id] || [];
    return n + chosen.filter((id) => !q.options.find((o) => o.id === id)?.exclusive).length;
  }, 0);

  return (
    <div
      className={`rounded-card border bg-ink overflow-hidden transition-opacity ${
        disabled ? "border-hairline opacity-40 pointer-events-none" : "border-hairline"
      }`}
    >
      <div className="flex items-center justify-between px-5 py-3 border-b border-hairline bg-surface">
        <div className="flex items-center gap-2.5">
          <span className="w-6 h-6 rounded-md bg-brand/15 text-brand grid place-items-center text-[11px] font-bold">
            3
          </span>
          <div>
            <h3 className="text-sm font-semibold text-txt">Rozhovor pred vyhodnotením</h3>
            <p className="text-[11px] text-txt3">Čo na recepte nie je — a práve tam býva riziko</p>
          </div>
        </div>
        <div className="text-[11px] text-txt3 tabular">
          {answered}/{questions.length} zodpovedaných
          {flagged > 0 && <span className="ml-2 text-warn">{flagged}× na kontrolu</span>}
        </div>
      </div>

      <div className="p-5">
        {error && <p className="text-xs text-bad mb-3">{error}</p>}

        <div className="space-y-5">
          {questions.map((q) => {
            const chosen = value[q.id] || [];
            return (
              <fieldset key={q.id}>
                <legend className="text-sm text-txt font-medium">{q.prompt}</legend>
                <p className="text-[11px] text-txt3 mt-0.5 mb-2.5">{q.hint}</p>
                <div className="flex flex-wrap gap-2">
                  {q.options.map((o) => {
                    const active = chosen.includes(o.id);
                    const neutral = o.exclusive;
                    return (
                      <button
                        key={o.id}
                        type="button"
                        aria-pressed={active}
                        onClick={() => toggle(q, o.id)}
                        className={`rounded-sm2 border px-3 py-1.5 text-xs transition-colors ${
                          active
                            ? neutral
                              ? "border-hairline2 bg-surface2 text-txt"
                              : "border-warn/40 bg-warn/10 text-warn"
                            : "border-hairline bg-surface text-txt2 hover:border-hairline2 hover:text-txt"
                        }`}
                      >
                        {o.label}
                      </button>
                    );
                  })}
                </div>
              </fieldset>
            );
          })}
        </div>

        <p className="mt-5 pt-4 border-t border-hairline text-[11px] text-txt3 leading-relaxed">
          Odpovede idú do rovnakého klinického enginu ako recept. Voľnopredajné lieky a
          doplnky sa kontrolujú na interakcie, duplicitu aj kumulatívne riziko — presne to,
          čo predpisujúci lekár nemá ako vedieť.
        </p>
      </div>
    </div>
  );
}
