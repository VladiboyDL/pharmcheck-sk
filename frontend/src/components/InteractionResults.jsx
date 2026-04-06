import InteractionCard from "./InteractionCard";

export default function InteractionResults({ data, onReset }) {
  if (!data) return null;

  const { interactions, safe_pairs, summary } = data;

  return (
    <div className="space-y-6">
      {/* Súhrnný panel */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-red-500 rounded-full" />
              <span className="text-sm font-medium text-gray-700">
                {summary.major} Závažná
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-amber-400 rounded-full" />
              <span className="text-sm font-medium text-gray-700">
                {summary.moderate} Stredná
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded-full" />
              <span className="text-sm font-medium text-gray-700">
                {summary.minor} Mierna
              </span>
            </div>
            <div className="text-sm text-gray-400">
              {summary.total_pairs_checked} párov skontrolovaných
            </div>
          </div>
          <button
            onClick={onReset}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium transition-colors"
          >
            Nová kontrola
          </button>
        </div>
      </div>

      {/* Varovanie pri závažných interakciách */}
      {summary.major > 0 && (
        <div className="bg-red-600 text-white rounded-xl p-4 flex items-center gap-3 shadow-md">
          <svg className="w-6 h-6 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2L1 21h22L12 2zm0 3.83L19.53 19H4.47L12 5.83zM11 16h2v2h-2v-2zm0-6h2v4h-2v-4z" />
          </svg>
          <div>
            <p className="font-semibold">
              {summary.major === 1
                ? "Nájdená 1 závažná interakcia"
                : `Nájdených ${summary.major} závažných interakcií`}
            </p>
            <p className="text-red-100 text-sm">
              {summary.major === 1
                ? "Táto kombinácia liekov vyžaduje okamžitú pozornosť."
                : "Tieto kombinácie liekov vyžadujú okamžitú pozornosť."}
            </p>
          </div>
        </div>
      )}

      {summary.major === 0 && summary.moderate === 0 && summary.minor === 0 && (
        <div className="bg-green-50 border border-green-200 text-green-800 rounded-xl p-4 flex items-center gap-3">
          <svg className="w-6 h-6 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
          </svg>
          <div>
            <p className="font-semibold">Žiadne interakcie</p>
            <p className="text-green-600 text-sm">
              Medzi zvolenými liekmi neboli nájdené žiadne klinicky významné
              interakcie.
            </p>
          </div>
        </div>
      )}

      {/* Karty interakcií */}
      {interactions.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
            Nájdené interakcie ({interactions.length})
          </h3>
          {interactions.map((interaction, idx) => (
            <InteractionCard key={idx} interaction={interaction} />
          ))}
        </div>
      )}

      {/* Bezpečné kombinácie */}
      {safe_pairs.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
            Bezpečné kombinácie ({safe_pairs.length})
          </h3>
          <div className="bg-white border border-gray-200 rounded-xl divide-y divide-gray-100">
            {safe_pairs.map((pair, idx) => (
              <div
                key={idx}
                className="px-4 py-3 flex items-center gap-3 text-sm"
              >
                <svg
                  className="w-4 h-4 text-green-500 flex-shrink-0"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
                </svg>
                <span className="text-gray-700">
                  {pair.drug_a} &harr; {pair.drug_b}
                </span>
                <span className="text-gray-400 text-xs ml-auto">
                  Bez interakcie
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
