export default function MedicationList({ drugs, onRemove, onDrugClick }) {
  if (drugs.length === 0) return null;

  return (
    <div className="bg-panel rounded-sm2 border border-hairline p-4">
      <h3 className="text-xs font-semibold text-txt2 uppercase tracking-wider mb-3">
        Zoznam liekov pacienta ({drugs.length})
      </h3>
      <div className="flex flex-wrap gap-2">
        {drugs.map((drug) => (
          <div
            key={drug.id}
            className="group flex items-center gap-2 bg-ink border border-hairline rounded-sm2 px-3 py-2 hover:border-brand hover:bg-brand/50 transition-all"
          >
            <button
              onClick={() => onDrugClick?.(drug)}
              className="text-left"
            >
              <span className="font-medium text-slate-800 text-sm hover:text-brand transition-colors">
                {drug.trade_name}
              </span>
              <span className="text-txt2 text-[10px] ml-1.5">
                {drug.active_substance}
              </span>
            </button>
            <button
              onClick={() => onRemove(drug.id)}
              className="ml-1 w-5 h-5 flex items-center justify-center rounded-full text-txt2 hover:text-bad hover:bg-surface transition-colors"
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
