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
      <div className="relative bg-panel rounded-card shadow-2xl w-full max-w-lg max-h-[85vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-panel border-b border-hairline px-6 py-4 flex items-center justify-between rounded-t-2xl">
          <h2 className="text-lg font-bold text-txt">Detail lieku</h2>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-sm2 hover:bg-surface2 transition-colors text-txt2 hover:text-txt3"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {loading ? (
          <div className="p-12 flex items-center justify-center">
            <div className="w-8 h-8 border-3 border-brand border-t-transparent rounded-full animate-spin" />
          </div>
        ) : drug ? (
          <div className="p-6 space-y-5">
            {/* Drug name */}
            <div>
              <h3 className="text-2xl font-bold text-txt">{drug.trade_name}</h3>
              <p className="text-sm text-txt3 mt-1">{drug.active_substance}</p>
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
                <h4 className="text-xs font-semibold text-txt2 uppercase tracking-wider mb-2">
                  Príbuzné lieky (rovnaká ATC skupina)
                </h4>
                <div className="space-y-1">
                  {drug.related_drugs.map((rd) => (
                    <div
                      key={rd.id}
                      className="flex items-center justify-between py-2 px-3 rounded-sm2 hover:bg-ink text-sm"
                    >
                      <div>
                        <span className="font-medium text-slate-800">{rd.trade_name}</span>
                        <span className="text-txt2 ml-2 text-xs">({rd.active_substance})</span>
                      </div>
                      {rd.strength && (
                        <span className="text-xs bg-surface2 text-txt3 px-2 py-0.5 rounded-full">
                          {rd.strength}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="pt-3 border-t border-hairline">
              {!isSelected ? (
                <button
                  onClick={() => onAdd(drug)}
                  className="w-full bg-brand text-txt font-semibold py-2.5 rounded-sm2 hover:bg-brandDeep transition-all"
                >
                  Pridať do kontroly interakcií
                </button>
              ) : (
                <div className="text-center text-sm text-ok font-medium py-2.5">
                  Liek je už pridaný do kontroly
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="p-12 text-center text-txt3">Liek sa nepodarilo načítať.</div>
        )}
      </div>
    </div>
  );
}

function InfoCard({ label, value, highlight }) {
  return (
    <div className="bg-ink rounded-sm2 p-3">
      <div className="text-[10px] text-txt2 uppercase tracking-wider font-semibold">{label}</div>
      <div className={`text-sm font-semibold mt-0.5 ${highlight ? "text-bad" : "text-txt"}`}>
        {value}
      </div>
    </div>
  );
}
