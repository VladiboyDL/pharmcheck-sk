export default function MedicationList({ drugs, onRemove, onDrugClick }) {
  if (drugs.length === 0) return null;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
      <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
        Zoznam liekov pacienta ({drugs.length})
      </h3>
      <div className="flex flex-wrap gap-2">
        {drugs.map((drug) => (
          <div
            key={drug.id}
            className="group flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 hover:border-blue-200 hover:bg-blue-50/50 transition-all"
          >
            <button
              onClick={() => onDrugClick?.(drug)}
              className="text-left"
            >
              <span className="font-medium text-slate-800 text-sm hover:text-blue-700 transition-colors">
                {drug.trade_name}
              </span>
              <span className="text-slate-400 text-[10px] ml-1.5">
                {drug.active_substance}
              </span>
            </button>
            <button
              onClick={() => onRemove(drug.id)}
              className="ml-1 w-5 h-5 flex items-center justify-center rounded-full text-slate-400 hover:text-red-500 hover:bg-red-50 transition-colors"
              title="Odstrániť"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
