import { useState } from "react";
import { explainInteraction } from "../api/client";

const VERDICT_STYLES = {
  DISPENSE: {
    ring: "border-emerald-700 bg-emerald-950/50",
    chip: "bg-emerald-500 text-emerald-950",
    text: "text-emerald-200",
    icon: "M5 13l4 4L19 7",
  },
  CONSULT: {
    ring: "border-amber-700 bg-amber-950/40",
    chip: "bg-amber-400 text-amber-950",
    text: "text-amber-200",
    icon: "M12 9v4m0 4h.01M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z",
  },
  BLOCK: {
    ring: "border-red-700 bg-red-950/50",
    chip: "bg-red-500 text-red-950",
    text: "text-red-200",
    icon: "M18.4 5.6L5.6 18.4M12 3a9 9 0 100 18 9 9 0 000-18z",
  },
};

const SEV = {
  critical: { label: "Kritické", dot: "bg-red-500", box: "border-red-900/70 bg-red-950/40", text: "text-red-200" },
  warning: { label: "Upozornenie", dot: "bg-amber-400", box: "border-amber-900/70 bg-amber-950/30", text: "text-amber-200" },
  info: { label: "Informácia", dot: "bg-sky-400", box: "border-sky-900/70 bg-sky-950/30", text: "text-sky-200" },
};

const IX_SEV = {
  "Závažná": { dot: "bg-red-500", text: "text-red-300", box: "border-red-900/70 bg-red-950/40" },
  "Stredná": { dot: "bg-amber-400", text: "text-amber-300", box: "border-slate-800 bg-slate-900/50" },
  "Mierna": { dot: "bg-slate-500", text: "text-slate-400", box: "border-slate-800 bg-slate-900/40" },
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
      <div className={`rounded-2xl border p-5 ${v.ring}`}>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-start gap-4 min-w-0">
            <div className={`w-12 h-12 rounded-xl grid place-items-center flex-shrink-0 ${v.chip}`}>
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" d={v.icon} />
              </svg>
            </div>
            <div className="min-w-0">
              <p className={`text-2xl font-bold tracking-tight ${v.text}`}>{data.verdict_label}</p>
              <p className="text-sm text-slate-400 mt-0.5">{data.verdict_reason}</p>
              {data.patient?.name && (
                <p className="text-xs text-slate-500 mt-1.5">
                  {data.patient.name} · {data.patient.age} r.
                  {data.patient.egfr != null && ` · eGFR ${data.patient.egfr} ml/min`}
                  {data.patient.pregnant && ` · gravidita ${data.patient.pregnancy_week}. týž.`}
                </p>
              )}
            </div>
          </div>
          <button
            onClick={onReset}
            className="rounded-lg border border-slate-700 hover:border-slate-500 text-slate-300 text-xs px-3 py-2 transition-colors"
          >
            Nový výdaj
          </button>
        </div>

        {/* Metrics strip */}
        <div className="mt-5 grid grid-cols-2 sm:grid-cols-4 gap-px rounded-xl overflow-hidden bg-slate-800/60">
          <Stat value={s.checks_run} label="kontrol vykonaných" />
          <Stat value={`${s.duration_ms} ms`} label="čas vyhodnotenia" />
          <Stat value={s.pairs_checked} label="liekových párov" />
          <Stat value={s.items} label="položiek receptu" />
        </div>

        <p className="mt-3 text-[11px] text-slate-500">
          Rovnaká kontrola ručne zaberie farmaceutovi približne{" "}
          <span className="text-slate-300 font-medium">{estimateManualMinutes(s)} minút</span> a pri
          bežnom objeme 200 receptov denne sa nerobí vôbec.
        </p>
      </div>

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
              <tr className="text-left text-slate-500 border-b border-slate-800">
                <th className="pb-2 font-medium">Prípravok</th>
                <th className="pb-2 font-medium">Účinná látka</th>
                <th className="pb-2 font-medium text-right">Sila</th>
                <th className="pb-2 font-medium text-right">Denne</th>
                <th className="pb-2 font-medium text-right">Denná dávka</th>
                <th className="pb-2 font-medium text-center">Stav</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/70">
              {data.items.map((it) => {
                const worst = worstSeverity(it.findings);
                return (
                  <tr key={it.id} className="align-top">
                    <td className="py-2 pr-3">
                      <span className="text-slate-200 font-medium">{it.trade_name}</span>
                      <span className="block text-[10px] text-slate-600 font-mono mt-0.5">{it.raw_line}</span>
                    </td>
                    <td className="py-2 pr-3 text-slate-400">{it.active_substance}</td>
                    <td className="py-2 pr-3 text-right text-slate-400 tabular-nums">
                      {it.strength_mg != null ? `${fmt(it.strength_mg)} mg` : "—"}
                    </td>
                    <td className="py-2 pr-3 text-right text-slate-400 tabular-nums">
                      {it.units_per_day != null ? `${fmt(it.units_per_day)}×` : "—"}
                    </td>
                    <td className="py-2 pr-3 text-right tabular-nums font-medium text-slate-200">
                      {it.daily_dose_mg != null ? `${fmt(it.daily_dose_mg)} mg` : "—"}
                    </td>
                    <td className="py-2 text-center">
                      {worst ? (
                        <span className={`inline-block w-2 h-2 rounded-full ${SEV[worst].dot}`} title={SEV[worst].label} />
                      ) : (
                        <span className="inline-block w-2 h-2 rounded-full bg-emerald-500" title="Bez nálezu" />
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {data.unresolved?.length > 0 && (
          <p className="mt-3 text-[11px] text-amber-400">
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

      {infos.length > 0 && <FindingGroup title="Informatívne zistenia" findings={infos} />}

      {/* ── Audit ───────────────────────────────────────────────────────────── */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 px-4 py-3">
        <div className="flex flex-wrap items-center justify-between gap-3 text-[11px]">
          <div className="flex items-center gap-2 text-slate-500">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeWidth="1.8" strokeLinecap="round" d="M9 12l2 2 4-4M12 3l7 4v5c0 4.5-3 8-7 9-4-1-7-4.5-7-9V7l7-4z" />
            </svg>
            Auditný záznam
          </div>
          <code className="text-slate-300 font-mono">{data.audit.audit_id}</code>
          <span className="text-slate-500 tabular-nums">{data.audit.timestamp.replace("T", " ")}</span>
          <span className="text-slate-500">{data.audit.operator}</span>
        </div>
      </div>
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
    <div className={`rounded-lg border px-3 py-2.5 ${st.box}`}>
      <button onClick={toggle} className="w-full flex items-start gap-2.5 text-left cursor-pointer">
        <span className={`mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0 ${st.dot}`} />
        <div className="min-w-0 flex-1">
          <p className="text-xs text-slate-200">
            <span className="font-medium">{ix.drug_a}</span>
            <span className="text-slate-500"> + </span>
            <span className="font-medium">{ix.drug_b}</span>
          </p>
          {!compact && !open && detail?.mechanism && (
            <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">{detail.mechanism}</p>
          )}
        </div>
        <span className={`text-[10px] font-semibold uppercase tracking-wide flex-shrink-0 ${st.text}`}>
          {ix.severity}
        </span>
        <svg
          className={`w-3.5 h-3.5 text-slate-600 flex-shrink-0 mt-0.5 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeWidth="2" strokeLinecap="round" d="M6 9l6 6 6-6" />
        </svg>
      </button>

      {open && (
        <dl className="mt-2.5 pt-2.5 border-t border-slate-800 space-y-2 text-[11px]">
          {loading && (
            <p className="flex items-center gap-2 text-slate-500">
              <span className="w-3 h-3 border-2 border-slate-600 border-t-cyan-400 rounded-full animate-spin" />
              Načítavam klinické vysvetlenie…
            </p>
          )}
          {failed && !detail && (
            <p className="text-slate-500">
              Vysvetlenie pre túto dvojicu zatiaľ nie je k dispozícii. Závažnosť pochádza z DDInter 2.0.
            </p>
          )}
          {detail?.mechanism && <Detail label="Mechanizmus" value={detail.mechanism} />}
          {detail?.management && <Detail label="Odporúčanie" value={detail.management} />}
          {detail?.alternatives && <Detail label="Alternatívy" value={detail.alternatives} />}
          {detail && (
            <p className="text-[10px] text-slate-600 pt-1">
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
      <dt className="text-slate-500 uppercase tracking-wider text-[9px]">{label}</dt>
      <dd className="text-slate-300 mt-0.5 leading-relaxed">{value}</dd>
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
            <div key={n} className={`rounded-lg border px-3.5 py-3 ${st.box}`}>
              <div className="flex items-start gap-2.5">
                <span className={`mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0 ${st.dot}`} />
                <div className="min-w-0">
                  <p className={`text-sm font-medium ${st.text}`}>{f.title}</p>
                  <p className="text-xs text-slate-400 mt-1 leading-relaxed">{f.detail}</p>
                  {f.action && (
                    <p className="text-[11px] text-slate-300 mt-2 flex items-start gap-1.5">
                      <svg className="w-3 h-3 mt-0.5 flex-shrink-0 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
    tone === "red" ? "border-red-900/60" : tone === "amber" ? "border-amber-900/60" : "border-slate-800";
  return (
    <section className={`rounded-2xl border bg-slate-950 ${border}`}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-5 py-3.5 text-left"
      >
        <div>
          <h3 className="text-sm font-semibold text-slate-100">{title}</h3>
          {subtitle && <p className="text-[11px] text-slate-500 mt-0.5">{subtitle}</p>}
        </div>
        <svg
          className={`w-4 h-4 text-slate-500 transition-transform ${open ? "rotate-180" : ""}`}
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
    <div className="bg-slate-950 px-3 py-3 text-center">
      <p className="text-lg font-bold text-slate-100 tabular-nums leading-none">{value}</p>
      <p className="text-[10px] text-slate-500 mt-1">{label}</p>
    </div>
  );
}

function worstSeverity(findings) {
  if (findings.some((f) => f.severity === "critical")) return "critical";
  if (findings.some((f) => f.severity === "warning")) return "warning";
  if (findings.some((f) => f.severity === "info")) return "info";
  return null;
}

function fmt(n) {
  return Number(n).toLocaleString("sk-SK", { maximumFractionDigits: 3 });
}

/** Rough manual-equivalent effort: ~20s per drug pair + ~40s per item dosing review. */
function estimateManualMinutes(s) {
  const seconds = s.pairs_checked * 20 + s.items * 40;
  return Math.max(1, Math.round(seconds / 60));
}
