import { useEffect, useMemo, useState } from "react";
import { Screen, Title, BigButton, Badge, Rail } from "./KioskShell";
import TakeAway from "./TakeAway";
import { notifyPrescriber } from "../../api/client";

/**
 * The outcome, paced one card at a time.
 *
 * A pharmacy dispenses valid prescriptions and counsels — it does not refuse a script
 * because two drugs interact. So the patient's first screen is their medicines being
 * ready, and the advice follows one point at a time, in plain language.
 */
export default function KioskOutcome({ data, onRestart, controls, onPageChange }) {
  const [page, setPage] = useState(0);

  const takeHome = data.items.filter((i) => i.source !== "interview" && i.status !== "verify");
  const plan = data.dosing_plan ?? [];
  const held = data.items.filter((i) => i.source !== "interview" && i.status === "verify");
  const declined = data.items.filter((i) => i.status === "decline");

  // One card per thing the patient has to hear, deduplicated and capped so a
  // seven-drug regimen does not turn into a fifteen-screen lecture.
  const cards = useMemo(() => {
    const out = [];
    const counselStep = (data.next_steps ?? []).find((s) => s.kind === "counsel");
    const forPatient = (counselStep?.script ?? []).filter((l) => l.patient_visible);
    for (const line of forPatient.slice(0, 2)) {
      out.push({
        kind: "advice",
        topic: line.topic,
        headline: line.title || line.topic,
        body: line.patient || line.say,
        notify: line.notify_prescriber === true,
      });
    }
    for (const r of data.resolutions ?? []) {
      out.push({
        kind: r.kind === "prescriber" ? "verify" : "swap",
        topic: r.item,
        headline: r.headline,
        body: r.detail,
        substitute: r.substitute,
        caveat: r.caveat,
      });
    }
    // Two or three things get remembered. Beyond that it is a lecture, and the
    // patient came here to leave with medicine.
    return out.slice(0, 2);
  }, [data]);

  // Meds + schedule, the advisories, then the take-away.
  const pages = 1 + cards.length + 1;
  const next = () => setPage((p) => Math.min(p + 1, pages - 1));

  // The voice agent steps through the same pages the button does.
  useEffect(() => {
    if (!controls) return;
    controls.current = { page, pages, last: page >= pages - 1, next };
    onPageChange?.(page);
    // onPageChange is a fresh arrow each render; it only needs to fire per page.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [controls, page, pages]);

  // ── Page 0: your medicines ────────────────────────────────────────────────
  if (page === 0) {
    // The take-away screen always follows, even with nothing to warn about — a clean
    // result is exactly the patient who should still leave with their schedule.
    return (
      <Screen
        footer={
          <div className="space-y-4">
            <BigButton onClick={next} full>
              Pokračovať
            </BigButton>
            <Rail steps={pages} current={0} />
          </div>
        }
      >
        <div className="text-center">
          <div className="w-20 h-20 rounded-card grid place-items-center mx-auto mb-6 bg-ok">
            <svg className="w-10 h-10 text-ink" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>

          <Title
            sub={
              held.length
                ? "Jeden liek si ešte overíme u vášho lekára, ostatné pripravuje výdajník."
                : "Výdajník ich pripravuje. Rozpis si o chvíľu odnesiete so sebou."
            }
          >
            {takeHome.length ? "Takto ich budete užívať" : "Musíme sa najprv spojiť s vaším lekárom"}
          </Title>

          {plan.length > 0 && (
            <ul className="mt-7 mx-auto max-w-lg space-y-2.5 text-left">
              {plan.map((entry) => (
                <li
                  key={entry.trade_name}
                  className="rounded-card border border-hairline bg-surface px-4 py-3.5"
                >
                  <div className="flex items-start gap-3">
                    <span className="w-6 h-6 rounded-sm2 bg-ok/15 text-ok grid place-items-center flex-shrink-0 mt-0.5">
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    </span>
                    <div className="min-w-0">
                      <p className="text-txt font-medium leading-tight">{entry.trade_name}</p>
                      <p className="text-brand text-sm mt-0.5">{entry.schedule}</p>
                      {entry.when && <p className="text-txt2 text-sm mt-0.5">{entry.when}</p>}
                      {entry.avoid && (
                        <p className="text-warn text-sm mt-0.5">{entry.avoid}</p>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </Screen>
    );
  }

  // ── Pages 1..n: one point at a time, the last one closes ──────────────────
  if (page <= cards.length) {
    const c = cards[page - 1];
    const last = false;
    return (
      <Screen
        footer={
          <div className="space-y-4">
            <BigButton onClick={last ? onRestart : next} full>
              {last ? "Rozumiem, ďakujem" : "Rozumiem"}
            </BigButton>
            <Rail steps={pages} current={page} />
          </div>
        }
      >
        <div className="text-center">
          <Badge tone={c.kind === "verify" ? "bad" : c.kind === "swap" ? "warn" : "slate"}>
            {c.kind === "verify" ? "Overujeme u lekára" : c.kind === "swap" ? "Odporúčame zmenu" : "Dobre vedieť"}
          </Badge>

          <div className="mt-5">
            <Title sub={c.body}>{c.headline}</Title>
          </div>

          {c.substitute && (
            <div className="mt-8 mx-auto max-w-sm rounded-card border-2 border-ok/40 bg-ok/10 p-5">
              <p className="text-[11px] font-mono uppercase tracking-[0.14em] text-ok">
                Dostanete namiesto toho
              </p>
              <p className="mt-1.5 text-2xl font-bold text-ok">{c.substitute.trade_name}</p>
              <p className="text-sm text-ok/80 mt-0.5">{c.substitute.active_substance}</p>
            </div>
          )}

          {c.caveat && <p className="mt-6 mx-auto max-w-md text-sm text-warn">{c.caveat}</p>}

          {c.kind === "advice" && (
            <>
              {c.notify && <NotifyPrescriber data={data} subject={c.topic} detail={c.body} />}
              <p className="mt-6 mx-auto max-w-md text-sm text-txt3">
                Lieky preto nevysadzujte ani si sami nemeňte dávku.
              </p>
            </>
          )}
        </div>
      </Screen>
    );
  }

  return <TakeAway data={data} onDone={onRestart} />;
}

/**
 * Sending the finding to the doctor who wrote the prescription.
 *
 * Telling a patient to "mention it next time" changes little; an asynchronous message
 * to the prescriber changed the prescription within a week in roughly a quarter of
 * cases. So this is an action, not a reminder.
 */
function NotifyPrescriber({ data, subject, detail }) {
  const [state, setState] = useState("idle"); // idle | sending | done

  async function send() {
    setState("sending");
    try {
      await notifyPrescriber({
        auditId: data.audit.audit_id,
        prescriber: data.prescriber,
        patient: data.patient?.name,
        subject,
        detail,
      });
    } catch {
      /* the queue is best-effort; the patient still leaves with the advice */
    }
    setState("done");
  }

  if (state === "done") {
    return (
      <div className="mt-6 mx-auto max-w-md rounded-card border border-ok/40 bg-ok/10 px-4 py-3 text-sm text-ok">
        Správu sme pripravili pre {data.prescriber || "vášho lekára"}.
      </div>
    );
  }

  return (
    <button
      onClick={send}
      disabled={state === "sending"}
      className="mt-6 mx-auto block rounded-card border-2 border-brand bg-brand/10 px-6 py-3.5 text-brand text-base hover:border-brand active:scale-[0.99] transition disabled:opacity-50"
    >
      {state === "sending" ? "Odosielam…" : "Upozorniť lekára, ktorý recept vystavil"}
    </button>
  );
}

function Line({ text, tone }) {
  const styles = {
    good: "border-ok/40 bg-ok/10 text-ok",
    warn: "border-warn/40 bg-warn/10 text-warn",
    bad: "border-bad/40 bg-bad/10 text-bad",
  };
  return <div className={`rounded-sm2 border px-4 py-3 text-sm ${styles[tone]}`}>{text}</div>;
}
