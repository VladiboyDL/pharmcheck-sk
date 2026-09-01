import { useState, useEffect } from "react";
import { browseATC } from "../api/client";

export default function ATCBrowser({ onAddDrug, onDrugClick, selectedIds }) {
  const [data, setData] = useState(null);
  const [path, setPath] = useState([]);
  const [loading, setLoading] = useState(true);

  const currentCode = path.length > 0 ? path[path.length - 1].code : "";

  useEffect(() => {
    setLoading(true);
    browseATC(currentCode)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [currentCode]);

  function navigateTo(code, name) {
    setPath((prev) => [...prev, { code, name }]);
  }

  function navigateBack(index) {
    setPath((prev) => prev.slice(0, index));
  }

  return (
    <div className="space-y-4">
      {/* Breadcrumbs */}
      <div className="bg-panel rounded-sm2 border border-hairline p-4">
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setPath([])}
            className={`text-sm font-medium transition-colors ${
              path.length === 0 ? "text-brand" : "text-txt3 hover:text-brand"
            }`}
          >
            ATC klasifikácia
          </button>
          {path.map((p, i) => (
            <div key={i} className="flex items-center gap-2">
              <svg className="w-4 h-4 text-txt2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              <button
                onClick={() => navigateBack(i + 1)}
                className={`text-sm font-medium transition-colors ${
                  i === path.length - 1 ? "text-brand" : "text-txt3 hover:text-brand"
                }`}
              >
                {p.name}
              </button>
            </div>
          ))}
        </div>
        <p className="text-xs text-txt2 mt-2">
          Anatomicko-terapeuticko-chemická klasifikácia liekov WHO
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="w-8 h-8 border-3 border-brand border-t-transparent rounded-full animate-spin" />
        </div>
      ) : data ? (
        <div className="space-y-4">
          {/* Sub-groups */}
          {data.groups.length > 0 && (
            <div className="grid gap-2 md:grid-cols-2">
              {data.groups.map((group) => (
                <button
                  key={group.code}
                  onClick={() => navigateTo(group.code, group.name)}
                  className="bg-panel border border-hairline rounded-sm2 p-4 text-left hover:border-brand hover: transition-all group"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-brand/15 rounded-sm2 flex items-center justify-center border border-brand">
                        <span className="text-sm font-bold text-brand">{group.code}</span>
                      </div>
                      <div>
                        <div className="font-medium text-slate-800 group-hover:text-brand transition-colors text-sm">
                          {group.name}
                        </div>
                        <div className="text-xs text-txt2">{group.drug_count} liekov</div>
                      </div>
                    </div>
                    <svg className="w-5 h-5 text-txt2 group-hover:text-brand transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Drug list */}
          {data.drugs.length > 0 && (
            <div className="bg-panel border border-hairline rounded-sm2 overflow-hidden">
              <div className="px-4 py-3 border-b border-hairline bg-ink">
                <h3 className="text-sm font-semibold text-txt3">
                  Lieky ({data.drugs.length})
                </h3>
              </div>
              <div className="divide-y divide-slate-50">
                {data.drugs.map((drug) => {
                  const alreadyAdded = selectedIds.has(drug.id);
                  return (
                    <div
                      key={drug.id}
                      className="flex items-center justify-between px-4 py-3 hover:bg-ink transition-colors"
                    >
                      <button
                        onClick={() => onDrugClick(drug)}
                        className="flex-1 text-left"
                      >
                        <span className="font-medium text-slate-800 text-sm hover:text-brand transition-colors">
                          {drug.trade_name}
                        </span>
                        <span className="text-txt2 ml-2 text-xs">
                          ({drug.active_substance})
                        </span>
                        {drug.strength && (
                          <span className="text-xs bg-surface2 text-txt3 px-1.5 py-0.5 rounded ml-2">
                            {drug.strength}
                          </span>
                        )}
                      </button>
                      <button
                        onClick={() => !alreadyAdded && onAddDrug(drug)}
                        disabled={alreadyAdded}
                        className={`text-xs font-medium px-3 py-1.5 rounded-sm2 transition-colors ${
                          alreadyAdded
                            ? "bg-surface text-ok cursor-default"
                            : "bg-brand/15 text-brand hover:bg-brand"
                        }`}
                      >
                        {alreadyAdded ? "Pridaný" : "Pridať"}
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {data.groups.length === 0 && data.drugs.length === 0 && (
            <div className="text-center py-12 text-txt2 text-sm">
              V tejto kategórii nie sú žiadne lieky.
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-12 text-txt2 text-sm">
          Nepodarilo sa načítať ATC klasifikáciu.
        </div>
      )}
    </div>
  );
}
