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

export default function InteractionCard({ interaction }) {
  const [expanded, setExpanded] = useState(false);
  const config = SEVERITY_CONFIG[interaction.severity] || FALLBACK;
  const isZavazna = interaction.severity === "Závažná";
  const isStredna = interaction.severity === "Stredná";

  return (
    <div
      className={`${config.bg} ${config.border} border rounded-xl overflow-hidden transition-all`}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left p-4 flex items-start gap-4"
      >
        <div className={`mt-0.5 ${config.icon}`}>
          {isZavazna ? (
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2L1 21h22L12 2zm0 3.83L19.53 19H4.47L12 5.83zM11 16h2v2h-2v-2zm0-6h2v4h-2v-4z" />
            </svg>
          ) : isStredna ? (
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
            </svg>
          ) : (
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
            </svg>
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-gray-900">
              {interaction.drug_a.trade_name}
            </span>
            <svg
              className="w-4 h-4 text-gray-400 flex-shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
              />
            </svg>
            <span className="font-semibold text-gray-900">
              {interaction.drug_b.trade_name}
            </span>
          </div>

          <p className="text-sm text-gray-500 mt-0.5">
            {interaction.drug_a.active_substance} &harr;{" "}
            {interaction.drug_b.active_substance}
          </p>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          <span
            className={`${config.badge} text-xs font-semibold px-2.5 py-1 rounded-full`}
          >
            {config.label}
          </span>
          <svg
            className={`w-5 h-5 text-gray-400 transition-transform ${
              expanded ? "rotate-180" : ""
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 pt-0 ml-10 space-y-3">
          {interaction.mechanism && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
                Mechanizmus
              </h4>
              <p className="text-sm text-gray-700 leading-relaxed">
                {interaction.mechanism}
              </p>
            </div>
          )}
          {interaction.management && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
                Odporúčanie
              </h4>
              <p className="text-sm text-gray-700 leading-relaxed">
                {interaction.management}
              </p>
            </div>
          )}
          {interaction.alternatives && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
                Alternatívy
              </h4>
              <p className="text-sm text-gray-700 leading-relaxed">
                {interaction.alternatives}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
