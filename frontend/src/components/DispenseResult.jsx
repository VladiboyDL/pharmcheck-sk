import { useState } from "react";
import { explainInteraction } from "../api/client";

const VERDICT_STYLES = {
  COUNSEL: {
    ring: "border-warn/40 bg-warn/10",
    chip: "bg-warn/15 text-warn",
    text: "text-warn",
    icon: "M8 10h.01M12 10h.01M16 10h.01M21 12a9 9 0 11-3.2-6.9L21 4l-.9 3.2A9 9 0 0121 12z",
  },
  VERIFY: {
    ring: "border-bad/40 bg-bad/10",
    chip: "bg-bad/15 text-bad",
    text: "text-bad",
    icon: "M3 5a2 2 0 012-2h3l2 5-2.5 1.5a11 11 0 005 5L14 12l5 2v3a2 2 0 01-2 2A14 14 0 013 5z",
  },
  PARTIAL: {
    ring: "border-warn/40 bg-warn/10",
    chip: "bg-warn/15 text-warn",
    text: "text-warn",
    icon: "M9 12h6m-3-3v6M12 3a9 9 0 100 18 9 9 0 000-18z",
  },
  DISPENSE: {
    ring: "border-ok/40 bg-ok/10",
    chip: "bg-ok/15 text-ok",
    text: "text-ok",
    icon: "M5 13l4 4L19 7",
  },
  CONSULT: {
    ring: "border-warn/40 bg-warn/10",
    chip: "bg-warn/15 text-warn",
    text: "text-warn",
    icon: "M12 9v4m0 4h.01M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z",
  },
  BLOCK: {
    ring: "border-bad/40 bg-bad/10",
    chip: "bg-bad/15 text-bad",
    text: "text-bad",
    icon: "M18.4 5.6L5.6 18.4M12 3a9 9 0 100 18 9 9 0 000-18z",
  },
};

const SEV = {
  critical: { label: "Kritické", dot: "bg-bad", box: "border-bad/40 bg-bad/10", text: "text-bad" },
  warning: { label: "Upozornenie", dot: "bg-warn", box: "border-warn/40 bg-warn/10", text: "text-warn" },
  info: { label: "Informácia", dot: "bg-brand", box: "border-brand/40 bg-brand/10", text: "text-brand" },
};

const IX_SEV = {
  "Závažná": { dot: "bg-bad", text: "text-bad", box: "border-bad/40 bg-bad/10" },
  "Stredná": { dot: "bg-warn", text: "text-warn", box: "border-hairline bg-surface" },
  "Mierna": { dot: "bg-slate-500", text: "text-txt2", box: "border-hairline bg-surface" },
};

export default function DispenseResult({ data, onReset }) {
  const v = VERDICT_STYLES[data.verdict] ?? VERDICT_STYLES.CONSULT;
  const s = data.summary;

  const itemFindings = data.items.flatMap((it) => it.findings.map((f) => ({ ...f, item: it })));
  const allFindings = [...itemFindings, ...data.findings];
  const critical = allFindings.filter((f) => f.severity === "critical");
  const warnings = allFindings.filter((f) => f.severity === "warning");
  const infos = allFindings.filter((f) => f.severity === "info");

  const majorIx = data.interactions.filter((i) => i.severity === "Závažná");
  const otherIx = data.interactions.filter((i) => i.severity !== "Závažná");

  return (
    <div className="space-y-4">
      {/* ── Verdict ─────────────────────────────────────────────────────────── */}
      <div className={`rounded-card border p-5 ${v.ring}`}>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-start gap-4 min-w-0">
            <div className={`w-12 h-12 rounded-sm2 grid place-items-center flex-shrink-0 ${v.chip}`}>
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" d={v.icon} />
              </svg>
            </div>
            <div className="min-w-0">
              <p className={`text-2xl font-bold tracking-tight ${v.text}`}>{data.verdict_label}</p>
              <p className="text-sm text-txt2 mt-0.5">{data.verdict_reason}</p>
              {data.patient?.name && (
                <p className="text-xs text-txt3 mt-1.5">
                  {data.patient.name} · {data.patient.age} r.
                  {data.patient.egfr != null && ` · eGFR ${data.patient.egfr} ml/min`}
                  {data.patient.pregnant && ` · gravidita ${data.patient.pregnancy_week}. týž.`}
                </p>
              )}
            </div>
          </div>
          <button
            onClick={onReset}
            className="rounded-sm2 border border-hairline2 hover:border-hairline2 text-txt2 text-xs px-3 py-2 transition-colors"
          >
            Nový výdaj
          </button>
        </div>

        {/* Metrics strip */}
        <div className="mt-5 grid grid-cols-2 sm:grid-cols-4 gap-px rounded-sm2 overflow-hidden bg-surface2">
          <Stat value={s.checks_run} label="kontrol vykonaných" />
          <Stat value={`${s.duration_ms} ms`} label="čas vyhodnotenia" />
          <Stat value={s.pairs_checked} label="liekových párov" />
          <Stat
            value={s.dispensable != null ? `${s.dispensable}/${s.items}` : s.items}
            label="položiek ide von"
          />
        </div>

        <p className="mt-3 text-[11px] text-txt3">
          Rovnaká kontrola ručne zaberie farmaceutovi približne{" "}
          <span className="text-txt2 font-medium">{estimateManualMinutes(s)} minút</span> a pri
          bežnom objeme 200 receptov denne sa nerobí vôbec.
        </p>
      </div>

      {/* ── What happens now ────────────────────────────────────────────────── */}
      {data.next_steps?.length > 0 && <NextSteps steps={data.next_steps} />}

      {/* ── Critical findings ───────────────────────────────────────────────── */}
      {critical.length > 0 && <FindingGroup title="Kritické zistenia" findings={critical} open />}

      {/* ── Major interactions ──────────────────────────────────────────────── */}
      {majorIx.length > 0 && (
        <Panel title={`Závažné liekové interakcie (${majorIx.length})`} tone="red" open>
          <div className="space-y-2.5">
            {majorIx.map((i, n) => (
              <InteractionRow key={n} ix={i} />
            ))}
          </div>
        </Panel>
      )}

      {warnings.length > 0 && <FindingGroup title="Upozornenia" findings={warnings} open />}

      {/* ── Prescription breakdown ──────────────────────────────────────────── */}
      <Panel title={`Rozpis receptu (${data.items.length})`} open>
        <div className="overflow-x-auto -mx-4 px-4">
          <table className="w-full text-xs min-w-[600px]">
            <thead>
              <tr className="text-left text-txt3 border-b border-hairline">
                <th className="pb-2 font-medium">Prípravok</th>
                <th className="pb-2 font-medium">Účinná látka</th>
                <th className="pb-2 font-medium text-right">Sila</th>
                <th className="pb-2 font-medium text-right">Denne</th>
                <th className="pb-2 font-medium text-right">Denná dávka</th>
                <th className="pb-2 font-medium text-right">Rozhodnutie</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-hairline">
              {data.items.map((it) => {
                const fromInterview = it.source === "interview";
                return (
                  <tr key={it.key} className="align-top">
                    <td className="py-2 pr-3">
                      <span className="text-txt font-medium">{it.trade_name}</span>
                      {fromInterview && (
                        <span className="ml-1.5 text-[9px] uppercase tracking-wide text-brand/80 border border-brand rounded px-1 py-px">
                          z rozhovoru
                        </span>
                      )}
                      <span className="block text-[10px] text-txt3 font-mono mt-0.5">{it.raw_line}</span>
                    </td>
                    <td className="py-2 pr-3 text-txt2">{it.active_substance}</td>
                    <td className="py-2 pr-3 text-right text-txt2 tabular">
                      {it.strength_mg != null ? `${fmt(it.strength_mg)} mg` : "—"}
                    </td>
                    <td className="py-2 pr-3 text-right text-txt2 tabular">
                      {it.units_per_day != null ? `${fmt(it.units_per_day)}×` : "—"}
                    </td>
                    <td className="py-2 pr-3 text-right tabular font-medium text-txt">
                      {it.daily_dose_mg != null ? `${fmt(it.daily_dose_mg)} mg` : "—"}
                    </td>
                    <td className="py-2 text-right">
                      <ItemStatus status={it.status} reasons={it.status_reasons} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {data.unresolved?.length > 0 && (
          <p className="mt-3 text-[11px] text-warn">
            Nerozpoznané riadky: {data.unresolved.join(" · ")}
          </p>
        )}
      </Panel>

      {/* ── Remaining interactions (alert-fatigue control) ──────────────────── */}
      {otherIx.length > 0 && (
        <Panel title={`Ostatné interakcie (${otherIx.length})`} subtitle="zoradené podľa klinickej významnosti">
          <div className="space-y-2">
            {otherIx.map((i, n) => (
              <InteractionRow key={n} ix={i} compact />
            ))}
          </div>
        </Panel>
      )}

      {data.unverified_pairs?.length > 0 && (
        <Panel
          title={`Neoverené dvojice (${data.unverified_pairs.length})`}
          subtitle="systém nevie potvrdiť ani vylúčiť interakciu"
          tone="amber"
        >
          <p className="text-xs text-txt2 mb-3 leading-relaxed">
            Tieto látky nie sú v interakčnej databáze. Absencia záznamu neznamená, že
            kombinácia je bezpečná — znamená, že o nej nemáme dáta.
          </p>
          <div className="space-y-1.5">
            {data.unverified_pairs.map((u, n) => (
              <div key={n} className="rounded-sm2 border border-hairline bg-surface px-3 py-2 text-xs">
                <span className="text-txt">
                  {u.drug_a} <span className="text-txt3">+</span> {u.drug_b}
                </span>
                <span className="block text-[10px] text-warn mt-0.5">
                  mimo databázy: {u.unknown.join(", ")}
                </span>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {infos.length > 0 && <FindingGroup title="Informatívne zistenia" findings={infos} />}

      {/* ── Audit ───────────────────────────────────────────────────────────── */}
      <div className="rounded-sm2 border border-hairline bg-surface px-4 py-3">
        <div className="flex flex-wrap items-center justify-between gap-3 text-[11px]">
          <div className="flex items-center gap-2 text-txt3">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeWidth="1.8" strokeLinecap="round" d="M9 12l2 2 4-4M12 3l7 4v5c0 4.5-3 8-7 9-4-1-7-4.5-7-9V7l7-4z" />
            </svg>
            Auditný záznam
          </div>
          <code className="text-txt2 font-mono">{data.audit.audit_id}</code>
          <span className="text-txt3 tabular">{data.audit.timestamp.replace("T", " ")}</span>
          <span className="text-txt3">{data.audit.operator}</span>
        </div>
      </div>
    </div>
  );
}

const STEP_STYLE = {
  dispense: { box: "border-ok/40 bg-ok/10", text: "text-ok", icon: "M5 13l4 4L19 7" },
  advise: { box: "border-ok/40 bg-ok/10", text: "text-ok", icon: "M5 13l4 4L19 7" },
  counsel: { box: "border-warn/40 bg-warn/10", text: "text-warn", icon: "M8 10h.01M12 10h.01M16 10h.01M21 12a9 9 0 11-3.2-6.9L21 4l-.9 3.2A9 9 0 0121 12z" },
  decline: { box: "border-warn/40 bg-orange-950/30", text: "text-warn", icon: "M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" },
  swap: { box: "border-warn/40 bg-warn/10", text: "text-warn", icon: "M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" },
  verify: { box: "border-bad/40 bg-bad/10", text: "text-bad", icon: "M3 5a2 2 0 012-2h3l2 5-2.5 1.5a11 11 0 005 5L14 12l5 2v3a2 2 0 01-2 2A14 14 0 013 5z" },
  contact: { box: "border-bad/40 bg-bad/10", text: "text-bad", icon: "M3 5a2 2 0 012-2h3l2 5-2.5 1.5a11 11 0 005 5L14 12l5 2v3a2 2 0 01-2 2A14 14 0 013 5z" },
};

/** The part a verdict alone never answers: what the patient does now. */
function NextSteps({ steps }) {
  return (
    <section className="rounded-card border border-hairline2 bg-panel/70">
      <div className="px-5 py-3.5 border-b border-hairline">
        <h3 className="text-sm font-semibold text-txt">Čo robiť teraz</h3>
        <p className="text-[11px] text-txt3 mt-0.5">
          Konkrétne kroky pri pulte — pacient neodchádza s prázdnymi rukami a bez plánu
        </p>
      </div>
      <div className="p-5 space-y-3">
        {steps.map((step, n) => {
          const st = STEP_STYLE[step.kind] ?? STEP_STYLE.swap;
          return (
            <div key={n} className={`rounded-sm2 border p-4 ${st.box}`}>
              <div className="flex items-start gap-3">
                <svg className={`w-4 h-4 mt-0.5 flex-shrink-0 ${st.text}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" d={st.icon} />
                </svg>
                <div className="min-w-0 flex-1">
                  <p className={`text-sm font-semibold ${st.text}`}>{step.title}</p>
                  <p className="text-xs text-txt2 mt-1 leading-relaxed">{step.detail}</p>
                  {step.script?.length > 0 && <CounsellingScript lines={step.script} />}
                  {step.message && <PrescriberMessage text={step.message} />}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

/** What to say at the window: the question first, then the professional action. */
function CounsellingScript({ lines }) {
  const [open, setOpen] = useState(true);
  const [all, setAll] = useState(false);
  // A pharmacist has about half a minute. Lead with the five that matter.
  const TOP = 5;
  const shown = all ? lines : lines.slice(0, TOP);
  return (
    <div className="mt-3">
      <button
        onClick={() => setOpen((o) => !o)}
        className="text-[11px] text-txt2 underline underline-offset-2 hover:text-txt"
      >
        {open ? "Skryť scenár rozhovoru" : `Zobraziť scenár rozhovoru (${lines.length})`}
      </button>
      {open && (
        <ol className="mt-2.5 space-y-2.5">
          {shown.map((l, n) => (
            <li key={n} className="rounded-sm2 bg-ink/70 border border-hairline p-3">
              <p className="text-[10px] font-mono uppercase tracking-[0.14em] text-txt3">{l.topic}</p>
              <p className="mt-1.5 text-sm text-txt">„{l.ask}“</p>
              {l.patient && (
                <p className="mt-1.5 text-xs text-txt2 leading-relaxed">
                  <span className="text-txt3">Pacientovi: </span>
                  {l.patient}
                </p>
              )}
              {l.say && (
                <p className="mt-1.5 text-xs text-brand/80 leading-relaxed">
                  <span className="text-txt3">Odborne: </span>
                  {l.say}
                </p>
              )}
            </li>
          ))}
        </ol>
      )}
      {open && lines.length > TOP && (
        <button
          onClick={() => setAll((a) => !a)}
          className="mt-2.5 text-[11px] text-brand hover:text-brand"
        >
          {all
            ? "Zobraziť len najdôležitejších 5"
            : `Zobraziť všetkých ${lines.length} — zoradené podľa významnosti`}
        </button>
      )}
    </div>
  );
}

function PrescriberMessage({ text }) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="mt-3">
      <div className="flex items-center gap-3">
        <button
          onClick={() => setOpen((o) => !o)}
          className="text-[11px] text-txt2 underline underline-offset-2 hover:text-txt"
        >
          {open ? "Skryť text pre lekára" : "Zobraziť pripravený text pre lekára"}
        </button>
        {open && (
          <button onClick={copy} className="text-[11px] text-brand hover:text-brand">
            {copied ? "skopírované" : "kopírovať"}
          </button>
        )}
      </div>
      {open && (
        <pre className="mt-2 whitespace-pre-wrap rounded-sm2 bg-ink border border-hairline p-3 text-[11px] text-txt2 leading-relaxed font-sans">
          {text}
        </pre>
      )}
    </div>
  );
}

const ITEM_STATUS = {
  dispense: { label: "Vydať", cls: "bg-ok/15 text-ok" },
  counsel: { label: "Vydať + poučiť", cls: "bg-warn/15 text-warn" },
  decline: { label: "Neodporúčať", cls: "bg-warn/15 text-warn" },
  verify: { label: "Overiť u lekára", cls: "bg-bad/15 text-bad" },
};

function ItemStatus({ status, reasons }) {
  const st = ITEM_STATUS[status] ?? ITEM_STATUS.dispense;
  return (
    <div className="inline-block text-right">
      <span className={`rounded px-2 py-0.5 text-[10px] font-semibold whitespace-nowrap ${st.cls}`}>
        {st.label}
      </span>
      {reasons?.length > 0 && (
        <span className="block text-[10px] text-txt3 mt-1 max-w-[15rem] text-right">
          {reasons[0]}
          {reasons.length > 1 && ` +${reasons.length - 1}`}
        </span>
      )}
    </div>
  );
}

function InteractionRow({ ix, compact }) {
  const [open, setOpen] = useState(false);
  const [detail, setDetail] = useState(
    ix.mechanism ? { mechanism: ix.mechanism, management: ix.management, alternatives: ix.alternatives, source: ix.source } : null
  );
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);
  const st = IX_SEV[ix.severity] ?? IX_SEV["Mierna"];

  // Clinical text is fetched on first open rather than during the dispense pass,
  // which keeps the verdict fast; DDInter ships severities without explanations.
  async function toggle() {
    const next = !open;
    setOpen(next);
    if (!next || detail || loading || failed) return;
    setLoading(true);
    try {
      const d = await explainInteraction({
        substanceA: ix.substance_a,
        substanceB: ix.substance_b,
        severity: ix.severity,
      });
      setDetail(d);
    } catch {
      setFailed(true);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={`rounded-sm2 border px-3 py-2.5 ${st.box}`}>
      <button onClick={toggle} className="w-full flex items-start gap-2.5 text-left cursor-pointer">
        <span className={`mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0 ${st.dot}`} />
        <div className="min-w-0 flex-1">
          <p className="text-xs text-txt">
            <span className="font-medium">{ix.drug_a}</span>
            <span className="text-txt3"> + </span>
            <span className="font-medium">{ix.drug_b}</span>
          </p>
          {!compact && !open && detail?.mechanism && (
            <p className="text-[11px] text-txt2 mt-1 line-clamp-2">{detail.mechanism}</p>
          )}
        </div>
        <span className={`text-[10px] font-semibold uppercase tracking-wide flex-shrink-0 ${st.text}`}>
          {ix.severity}
        </span>
        <svg
          className={`w-3.5 h-3.5 text-txt3 flex-shrink-0 mt-0.5 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeWidth="2" strokeLinecap="round" d="M6 9l6 6 6-6" />
        </svg>
      </button>

      {open && (
        <dl className="mt-2.5 pt-2.5 border-t border-hairline space-y-2 text-[11px]">
          {loading && (
            <p className="flex items-center gap-2 text-txt3">
              <span className="w-3 h-3 border-2 border-hairline2 border-t-brand rounded-full animate-spin" />
              Načítavam klinické vysvetlenie…
            </p>
          )}
          {failed && !detail && (
            <p className="text-txt3">
              Vysvetlenie pre túto dvojicu zatiaľ nie je k dispozícii. Závažnosť pochádza z DDInter 2.0.
            </p>
          )}
          {detail?.mechanism && <Detail label="Mechanizmus" value={detail.mechanism} />}
          {detail?.management && <Detail label="Odporúčanie" value={detail.management} />}
          {detail?.alternatives && <Detail label="Alternatívy" value={detail.alternatives} />}
          {detail && (
            <p className="text-[10px] text-txt3 pt-1">
              Zdroj: {detail.source === "ai" ? "AI analýza (uložené do databázy)" : "DDInter 2.0"}
            </p>
          )}
        </dl>
      )}
    </div>
  );
}

function Detail({ label, value }) {
  return (
    <div>
      <dt className="text-txt3 uppercase tracking-wider text-[9px]">{label}</dt>
      <dd className="text-txt2 mt-0.5 leading-relaxed">{value}</dd>
    </div>
  );
}

function FindingGroup({ title, findings, open: defaultOpen }) {
  const tone = findings[0]?.severity === "critical" ? "red" : findings[0]?.severity === "warning" ? "amber" : "slate";
  return (
    <Panel title={`${title} (${findings.length})`} tone={tone} open={defaultOpen}>
      <div className="space-y-2.5">
        {findings.map((f, n) => {
          const st = SEV[f.severity];
          return (
            <div key={n} className={`rounded-sm2 border px-3.5 py-3 ${st.box}`}>
              <div className="flex items-start gap-2.5">
                <span className={`mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0 ${st.dot}`} />
                <div className="min-w-0">
                  <p className={`text-sm font-medium ${st.text}`}>{f.title}</p>
                  <p className="text-xs text-txt2 mt-1 leading-relaxed">{f.detail}</p>
                  {f.action && (
                    <p className="text-[11px] text-txt2 mt-2 flex items-start gap-1.5">
                      <svg className="w-3 h-3 mt-0.5 flex-shrink-0 text-txt3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeWidth="2" strokeLinecap="round" d="M13 7l5 5-5 5M6 12h12" />
                      </svg>
                      {f.action}
                    </p>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Panel>
  );
}

function Panel({ title, subtitle, tone = "slate", open: defaultOpen = false, children }) {
  const [open, setOpen] = useState(defaultOpen);
  const border =
    tone === "red" ? "border-bad/40" : tone === "amber" ? "border-warn/40" : "border-hairline";
  return (
    <section className={`rounded-card border bg-ink ${border}`}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-5 py-3.5 text-left"
      >
        <div>
          <h3 className="text-sm font-semibold text-txt">{title}</h3>
          {subtitle && <p className="text-[11px] text-txt3 mt-0.5">{subtitle}</p>}
        </div>
        <svg
          className={`w-4 h-4 text-txt3 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeWidth="2" strokeLinecap="round" d="M6 9l6 6 6-6" />
        </svg>
      </button>
      {open && <div className="px-5 pb-5">{children}</div>}
    </section>
  );
}

function Stat({ value, label }) {
  return (
    <div className="bg-ink px-3 py-3 text-center">
      <p className="text-2xl font-mono text-txt tabular leading-none">{value}</p>
      <p className="text-[10px] text-txt3 mt-1">{label}</p>
    </div>
  );
}

function fmt(n) {
  return Number(n).toLocaleString("sk-SK", { maximumFractionDigits: 3 });
}

/** Rough manual-equivalent effort: ~20s per drug pair + ~40s per item dosing review. */
function estimateManualMinutes(s) {
  const seconds = s.pairs_checked * 20 + s.items * 40;
  return Math.max(1, Math.round(seconds / 60));
}
