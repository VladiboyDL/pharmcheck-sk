import { useState } from "react";

const SEVERITY_CONFIG = {
  "Závažná": {
    bg: "bg-red-50",
    border: "border-red-200",
    badge: "bg-red-600 text-white",
    icon: "text-red-600",
    label: "Závažná",
  },
  "Stredná": {
    bg: "bg-amber-50",
    border: "border-amber-200",
    badge: "bg-amber-500 text-white",
    icon: "text-amber-600",
    label: "Stredná",
  },
  "Mierna": {
    bg: "bg-green-50",
    border: "border-green-200",
    badge: "bg-green-600 text-white",
    icon: "text-green-600",
    label: "Mierna",
  },
};

const FALLBACK = SEVERITY_CONFIG["Mierna"];

export default function InteractionCard({ interaction, onDrugClick, onResolve }) {
  const [expanded, setExpanded] = useState(false);
  const config = SEVERITY_CONFIG[interaction.severity] || FALLBACK;
  const isZavazna = interaction.severity === "Závažná";
  const isStredna = interaction.severity === "Stredná";

  return (
    <div className={`${config.bg} ${config.border} border rounded-xl overflow-hidden transition-all print:break-inside-avoid`}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left p-4 flex items-start gap-3"
      >
        <div className={`mt-0.5 ${config.icon} flex-shrink-0`}>
          {isZavazna ? (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2L1 21h22L12 2zm0 3.83L19.53 19H4.47L12 5.83zM11 16h2v2h-2v-2zm0-6h2v4h-2v-4z" />
            </svg>
          ) : isStredna ? (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
            </svg>
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className="font-semibold text-slate-900 hover:text-blue-700 transition-colors cursor-pointer text-sm"
              onClick={(e) => {
                e.stopPropagation();
                onDrugClick?.(interaction.drug_a);
              }}
            >
              {interaction.drug_a.trade_name}
            </span>
            <svg className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
            </svg>
            <span
              className="font-semibold text-slate-900 hover:text-blue-700 transition-colors cursor-pointer text-sm"
              onClick={(e) => {
                e.stopPropagation();
                onDrugClick?.(interaction.drug_b);
              }}
            >
              {interaction.drug_b.trade_name}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            {interaction.drug_a.active_substance} &harr; {interaction.drug_b.active_substance}
          </p>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          {interaction.source && interaction.source !== "db" && (
            <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-violet-100 text-violet-700 border border-violet-200" title="Interakcia identifikovaná AI">
              AI
            </span>
          )}
          <span className={`${config.badge} text-[10px] font-semibold px-2 py-1 rounded-full`}>
            {config.label}
          </span>
          <svg
            className={`w-4 h-4 text-slate-400 transition-transform print:hidden ${expanded ? "rotate-180" : ""}`}
            fill="none" stroke="currentColor" viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {(expanded || false) && (
        <div className="px-4 pb-4 pt-0 ml-8 space-y-3 print:block">
          {interaction.mechanism && (
            <DetailSection title="Mechanizmus" text={interaction.mechanism} />
          )}
          {interaction.management && (
            <DetailSection title="Odporúčanie" text={interaction.management} />
          )}
          {interaction.alternatives && (
            <DetailSection title="Alternatívy" text={interaction.alternatives} />
          )}

          {/* Resolver button */}
          {(isZavazna || isStredna) && onResolve && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onResolve();
              }}
              className="mt-2 text-xs font-medium text-blue-600 hover:text-blue-800 px-3 py-2 rounded-lg bg-blue-50 hover:bg-blue-100 transition-colors flex items-center gap-1.5 print:hidden"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
              Nájsť alternatívu
            </button>
          )}
        </div>
      )}
    </div>
  );
}

function DetailSection({ title, text }) {
  return (
    <div>
      <h4 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
        {title}
      </h4>
      <p className="text-sm text-slate-700 leading-relaxed">{text}</p>
    </div>
  );
}
