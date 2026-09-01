import { useMemo, useState } from "react";
import { Screen, Title, BigButton, Badge, Rail } from "./KioskShell";
import TakeAway from "./TakeAway";

/**
 * The outcome, paced one card at a time.
 *
 * A pharmacy dispenses valid prescriptions and counsels — it does not refuse a script
 * because two drugs interact. So the patient's first screen is their medicines being
 * ready, and the advice follows one point at a time, in plain language.
 */
export default function KioskOutcome({ data, onRestart }) {
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
    for (const line of (counselStep?.script ?? []).slice(0, 2)) {
      out.push({ kind: "advice", topic: line.topic, ask: line.ask, body: line.patient || line.say });
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

  // ── Page 0: your medicines ────────────────────────────────────────────────
  if (page === 0) {
    const nothingToSay = cards.length === 0;
    return (
      <Screen
        footer={
          <div className="space-y-4">
            <BigButton onClick={nothingToSay ? onRestart : next} full>
              {nothingToSay ? "Hotovo, ďakujem" : "Pokračovať"}
            </BigButton>
            <Rail steps={pages} current={0} />
          </div>
        }
      >
        <div className="text-center">
          <div className="w-20 h-20 rounded-3xl grid place-items-center mx-auto mb-6 bg-emerald-500">
            <svg className="w-10 h-10 text-slate-950" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>

          <Title
            sub={
              held.length
                ? "Jeden liek si ešte overíme u vášho lekára, ostatné sú pripravené."
                : "Lieky sú pripravené. Rozpis si o chvíľu odnesiete so sebou."
            }
          >
            {takeHome.length ? "Takto ich budete užívať" : "Musíme sa najprv spojiť s vaším lekárom"}
          </Title>

          {plan.length > 0 && (
            <ul className="mt-7 mx-auto max-w-lg space-y-2.5 text-left">
              {plan.map((entry) => (
                <li
                  key={entry.trade_name}
                  className="rounded-2xl border border-slate-800 bg-slate-900/60 px-4 py-3.5"
                >
                  <div className="flex items-start gap-3">
                    <span className="w-6 h-6 rounded-lg bg-emerald-500/15 text-emerald-300 grid place-items-center flex-shrink-0 mt-0.5">
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    </span>
                    <div className="min-w-0">
                      <p className="text-slate-100 font-medium leading-tight">{entry.trade_name}</p>
                      <p className="text-cyan-300 text-sm mt-0.5">{entry.schedule}</p>
                      {entry.when && <p className="text-slate-400 text-sm mt-0.5">{entry.when}</p>}
                      {entry.avoid && (
                        <p className="text-amber-300/90 text-sm mt-0.5">{entry.avoid}</p>
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
            <Title sub={c.body}>{c.headline || c.ask}</Title>
          </div>

          {c.substitute && (
            <div className="mt-8 mx-auto max-w-sm rounded-2xl border-2 border-emerald-700 bg-emerald-950/40 p-5">
              <p className="text-[11px] uppercase tracking-wider text-emerald-400">
                Dostanete namiesto toho
              </p>
              <p className="mt-1.5 text-2xl font-bold text-emerald-100">{c.substitute.trade_name}</p>
              <p className="text-sm text-emerald-300/80 mt-0.5">{c.substitute.active_substance}</p>
            </div>
          )}

          {c.caveat && <p className="mt-6 mx-auto max-w-md text-sm text-amber-300/90">{c.caveat}</p>}

          {c.kind === "advice" && (
            <p className="mt-7 mx-auto max-w-md text-sm text-slate-500">
              Nie je to dôvod liek nebrať. Spomeňte to prosím lekárovi pri najbližšej návšteve.
            </p>
          )}
        </div>
      </Screen>
    );
  }

  return <TakeAway data={data} onDone={onRestart} />;
}

function Line({ text, tone }) {
  const styles = {
    good: "border-emerald-900 bg-emerald-950/30 text-emerald-200",
    warn: "border-amber-900 bg-amber-950/25 text-amber-200",
    bad: "border-red-900 bg-red-950/30 text-red-200",
  };
  return <div className={`rounded-xl border px-4 py-3 text-sm ${styles[tone]}`}>{text}</div>;
}
