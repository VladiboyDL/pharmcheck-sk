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
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setPath([])}
            className={`text-sm font-medium transition-colors ${
              path.length === 0 ? "text-blue-600" : "text-slate-500 hover:text-blue-600"
            }`}
          >
            ATC klasifikácia
          </button>
          {path.map((p, i) => (
            <div key={i} className="flex items-center gap-2">
              <svg className="w-4 h-4 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              <button
                onClick={() => navigateBack(i + 1)}
                className={`text-sm font-medium transition-colors ${
                  i === path.length - 1 ? "text-blue-600" : "text-slate-500 hover:text-blue-600"
                }`}
              >
                {p.name}
              </button>
            </div>
          ))}
        </div>
        <p className="text-xs text-slate-400 mt-2">
          Anatomicko-terapeuticko-chemická klasifikácia liekov WHO
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="w-8 h-8 border-3 border-blue-500 border-t-transparent rounded-full animate-spin" />
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
                  className="bg-white border border-slate-200 rounded-xl p-4 text-left hover:border-blue-300 hover:shadow-md transition-all group"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg flex items-center justify-center border border-blue-100">
                        <span className="text-sm font-bold text-blue-700">{group.code}</span>
                      </div>
                      <div>
                        <div className="font-medium text-slate-800 group-hover:text-blue-700 transition-colors text-sm">
                          {group.name}
                        </div>
                        <div className="text-xs text-slate-400">{group.drug_count} liekov</div>
                      </div>
                    </div>
                    <svg className="w-5 h-5 text-slate-300 group-hover:text-blue-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Drug list */}
          {data.drugs.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-100 bg-slate-50">
                <h3 className="text-sm font-semibold text-slate-700">
                  Lieky ({data.drugs.length})
                </h3>
              </div>
              <div className="divide-y divide-slate-50">
                {data.drugs.map((drug) => {
                  const alreadyAdded = selectedIds.has(drug.id);
                  return (
                    <div
                      key={drug.id}
                      className="flex items-center justify-between px-4 py-3 hover:bg-slate-50 transition-colors"
                    >
                      <button
                        onClick={() => onDrugClick(drug)}
                        className="flex-1 text-left"
                      >
                        <span className="font-medium text-slate-800 text-sm hover:text-blue-600 transition-colors">
                          {drug.trade_name}
                        </span>
                        <span className="text-slate-400 ml-2 text-xs">
                          ({drug.active_substance})
                        </span>
                        {drug.strength && (
                          <span className="text-xs bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded ml-2">
                            {drug.strength}
                          </span>
                        )}
                      </button>
                      <button
                        onClick={() => !alreadyAdded && onAddDrug(drug)}
                        disabled={alreadyAdded}
                        className={`text-xs font-medium px-3 py-1.5 rounded-lg transition-colors ${
                          alreadyAdded
                            ? "bg-green-50 text-green-600 cursor-default"
                            : "bg-blue-50 text-blue-600 hover:bg-blue-100"
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
            <div className="text-center py-12 text-slate-400 text-sm">
              V tejto kategórii nie sú žiadne lieky.
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-12 text-slate-400 text-sm">
          Nepodarilo sa načítať ATC klasifikáciu.
        </div>
      )}
    </div>
  );
}
