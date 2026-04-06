export default function MedicationList({ drugs, onRemove }) {
  if (drugs.length === 0) return null;

  return (
    <div className="mt-4">
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
        Zoznam liekov pacienta ({drugs.length})
      </h3>
      <div className="flex flex-wrap gap-2">
        {drugs.map((drug) => (
          <div
            key={drug.id}
            className="group flex items-center gap-2 bg-white border border-gray-200 rounded-lg px-3 py-2 shadow-sm hover:shadow-md transition-all"
          >
            <div>
              <span className="font-medium text-gray-800 text-sm">
                {drug.trade_name}
              </span>
              <span className="text-gray-400 text-xs ml-1.5">
                {drug.active_substance}
              </span>
            </div>
            <button
              onClick={() => onRemove(drug.id)}
              className="ml-1 w-5 h-5 flex items-center justify-center rounded-full text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
              title="Odstrániť"
            >
              <svg
                className="w-3.5 h-3.5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
