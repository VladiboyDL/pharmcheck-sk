import { useState, useEffect } from "react";
import { getDrugDetail } from "../api/client";

export default function DrugDetailModal({ drugId, onClose, onAdd, isSelected }) {
  const [drug, setDrug] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getDrugDetail(drugId)
      .then(setDrug)
      .catch(() => setDrug(null))
      .finally(() => setLoading(false));
  }, [drugId]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[85vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-slate-100 px-6 py-4 flex items-center justify-between rounded-t-2xl">
          <h2 className="text-lg font-bold text-slate-900">Detail lieku</h2>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-slate-100 transition-colors text-slate-400 hover:text-slate-600"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {loading ? (
          <div className="p-12 flex items-center justify-center">
            <div className="w-8 h-8 border-3 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : drug ? (
          <div className="p-6 space-y-5">
            {/* Drug name */}
            <div>
              <h3 className="text-2xl font-bold text-slate-900">{drug.trade_name}</h3>
              <p className="text-sm text-slate-500 mt-1">{drug.active_substance}</p>
            </div>

            {/* Info grid */}
            <div className="grid grid-cols-2 gap-3">
              <InfoCard label="ATC kód" value={drug.atc_code || "—"} />
              <InfoCard label="ATC skupina" value={drug.atc_group || "—"} />
              <InfoCard label="Sila" value={drug.strength || "—"} />
              <InfoCard label="Forma" value={drug.form || "—"} />
              {drug.sukl_code && <InfoCard label="ŠÚKL kód" value={drug.sukl_code} />}
              <InfoCard
                label="Interakcie"
                value={drug.interaction_count}
                highlight={drug.interaction_count > 0}
              />
            </div>

            {/* Related drugs */}
            {drug.related_drugs.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Príbuzné lieky (rovnaká ATC skupina)
                </h4>
                <div className="space-y-1">
                  {drug.related_drugs.map((rd) => (
                    <div
                      key={rd.id}
                      className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-slate-50 text-sm"
                    >
                      <div>
                        <span className="font-medium text-slate-800">{rd.trade_name}</span>
                        <span className="text-slate-400 ml-2 text-xs">({rd.active_substance})</span>
                      </div>
                      {rd.strength && (
                        <span className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full">
                          {rd.strength}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="pt-3 border-t border-slate-100">
              {!isSelected ? (
                <button
                  onClick={() => onAdd(drug)}
                  className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold py-2.5 rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all"
                >
                  Pridať do kontroly interakcií
                </button>
              ) : (
                <div className="text-center text-sm text-green-600 font-medium py-2.5">
                  Liek je už pridaný do kontroly
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="p-12 text-center text-slate-500">Liek sa nepodarilo načítať.</div>
        )}
      </div>
    </div>
  );
}

function InfoCard({ label, value, highlight }) {
  return (
    <div className="bg-slate-50 rounded-lg p-3">
      <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">{label}</div>
      <div className={`text-sm font-semibold mt-0.5 ${highlight ? "text-red-600" : "text-slate-900"}`}>
        {value}
      </div>
    </div>
  );
}
