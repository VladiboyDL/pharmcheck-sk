import { useState } from "react";
import InteractionCard from "./InteractionCard";
import InteractionResolver from "./InteractionResolver";

export default function InteractionResults({ data, medications, onReset, onDrugClick }) {
  const [severityFilter, setSeverityFilter] = useState("all");
  const [showResolver, setShowResolver] = useState(false);
  const [resolverDrug, setResolverDrug] = useState(null);

  if (!data) return null;

  const { interactions, safe_pairs, summary, ai_enabled } = data;
  const aiCount = interactions.filter((i) => i.source === "ai" || i.source === "ai_cached").length;

  const filtered = severityFilter === "all"
    ? interactions
    : interactions.filter((i) => i.severity === severityFilter);

  function handlePrint() {
    window.print();
  }

  function handleResolve(interaction) {
    // Find the drug that has the most interactions - suggest replacing it
    const drugA = medications.find(
      (m) => m.trade_name === interaction.drug_a.trade_name
    );
    if (drugA) {
      setResolverDrug(drugA);
      setShowResolver(true);
    }
  }

  return (
    <div className="space-y-4 print:space-y-2">
      {/* Summary bar */}
      <div className="bg-panel rounded-sm2 border border-hairline p-4 print:shadow-none print:border-hairline2">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-4">
            <SeverityDot color="red" count={summary.major} label="Závažná" onClick={() => setSeverityFilter(severityFilter === "Závažná" ? "all" : "Závažná")} active={severityFilter === "Závažná"} />
            <SeverityDot color="amber" count={summary.moderate} label="Stredná" onClick={() => setSeverityFilter(severityFilter === "Stredná" ? "all" : "Stredná")} active={severityFilter === "Stredná"} />
            <SeverityDot color="green" count={summary.minor} label="Mierna" onClick={() => setSeverityFilter(severityFilter === "Mierna" ? "all" : "Mierna")} active={severityFilter === "Mierna"} />
            <div className="text-xs text-txt2 hidden sm:block">
              {summary.total_pairs_checked} párov
            </div>
            {ai_enabled && (
              <div className="flex items-center gap-1.5 text-xs print:hidden">
                <span className="bg-violet-100 text-violet-700 font-bold px-1.5 py-0.5 rounded text-[9px] border border-violet-200">AI</span>
                <span className="text-violet-600 font-medium">
                  {aiCount > 0 ? `${aiCount} nájdených AI` : "aktívne"}
                </span>
              </div>
            )}
          </div>
          <div className="flex items-center gap-2 print:hidden">
            <button
              onClick={handlePrint}
              className="text-xs text-txt3 hover:text-txt3 font-medium px-3 py-1.5 rounded-sm2 hover:bg-surface2 transition-colors flex items-center gap-1.5"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
              </svg>
              Tlačiť
            </button>
            <button
              onClick={onReset}
              className="text-xs text-brand hover:text-txt font-medium px-3 py-1.5 rounded-sm2 hover:bg-brand/15 transition-colors"
            >
              Nová kontrola
            </button>
          </div>
        </div>
      </div>

      {/* Print header */}
      <div className="hidden print:block">
        <h2 className="text-lg font-bold">PharmCheck SK - Správa o interakciách</h2>
        <p className="text-sm text-txt3">
          Dátum: {new Date().toLocaleDateString("sk-SK")} &middot; Lieky: {medications.map((m) => m.trade_name).join(", ")}
        </p>
      </div>

      {/* Major warning banner */}
      {summary.major > 0 && (
        <div className="rounded-sm2 border border-bad/40 bg-bad/10 p-4 flex items-center gap-3 text-bad print:border print:bg-surface">
          <svg className="w-6 h-6 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2L1 21h22L12 2zm0 3.83L19.53 19H4.47L12 5.83zM11 16h2v2h-2v-2zm0-6h2v4h-2v-4z" />
          </svg>
          <div>
            <p className="font-semibold text-txt">
              {summary.major === 1
                ? "Nájdená 1 závažná interakcia"
                : `Nájdených ${summary.major} závažných interakcií`}
            </p>
            <p className="text-txt2 text-sm">
              Zvážte úpravu medikácie. Kliknite na "Nájsť alternatívu" pri interakcii.
            </p>
          </div>
        </div>
      )}

      {/* No interactions */}
      {summary.major === 0 && summary.moderate === 0 && summary.minor === 0 && (
        <div className="bg-surface border border-ok/40 text-ok rounded-sm2 p-4 flex items-center gap-3">
          <svg className="w-6 h-6 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
          </svg>
          <div>
            <p className="font-semibold">Žiadne interakcie</p>
            <p className="text-ok text-sm">
              Medzi zvolenými liekmi neboli nájdené žiadne klinicky významné interakcie.
            </p>
          </div>
        </div>
      )}

      {/* Interaction cards */}
      {filtered.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-txt2 uppercase tracking-wider">
              {severityFilter === "all"
                ? `Nájdené interakcie (${interactions.length})`
                : `${severityFilter} interakcie (${filtered.length})`}
            </h3>
            {severityFilter !== "all" && (
              <button
                onClick={() => setSeverityFilter("all")}
                className="text-xs text-brand hover:text-brand print:hidden"
              >
                Zobraziť všetky
              </button>
            )}
          </div>
          {filtered.map((interaction, idx) => (
            <InteractionCard
              key={idx}
              interaction={interaction}
              onDrugClick={onDrugClick}
              onResolve={() => handleResolve(interaction)}
            />
          ))}
        </div>
      )}

      {/* Safe pairs */}
      {safe_pairs.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-txt2 uppercase tracking-wider mb-3">
            Bezpečné kombinácie ({safe_pairs.length})
          </h3>
          <div className="bg-panel border border-hairline rounded-sm2 divide-y divide-slate-50">
            {safe_pairs.map((pair, idx) => (
              <div key={idx} className="px-4 py-2.5 flex items-center gap-3 text-sm">
                <svg className="w-4 h-4 text-green-500 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
                </svg>
                <span className="text-txt3">
                  {pair.drug_a} &harr; {pair.drug_b}
                </span>
                <span className="text-txt2 text-xs ml-auto">OK</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Resolver modal */}
      {showResolver && resolverDrug && (
        <InteractionResolver
          drug={resolverDrug}
          contextDrugIds={medications.filter((m) => m.id !== resolverDrug.id).map((m) => m.id)}
          onClose={() => {
            setShowResolver(false);
            setResolverDrug(null);
          }}
        />
      )}
    </div>
  );
}

function SeverityDot({ color, count, label, onClick, active }) {
  const colorClasses = {
    red: "bg-bad",
    amber: "bg-warn",
    green: "bg-green-500",
  };

  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 px-2 py-1 rounded-full transition-colors print:cursor-default ${
        active ? "bg-surface2 ring-1 ring-slate-300" : "hover:bg-ink"
      }`}
    >
      <div className={`w-2.5 h-2.5 ${colorClasses[color]} rounded-full`} />
      <span className="text-sm font-medium text-txt3">
        {count} {label}
      </span>
    </button>
  );
}
