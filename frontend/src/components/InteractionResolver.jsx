import { useState, useEffect } from "react";
import { getAlternatives } from "../api/client";

export default function InteractionResolver({ drug, contextDrugIds, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getAlternatives(drug.id, contextDrugIds)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [drug.id, contextDrugIds.join(",")]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-panel rounded-card shadow-2xl w-full max-w-lg max-h-[85vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-panel border-b border-hairline px-6 py-4 flex items-center justify-between rounded-t-2xl">
          <div>
            <h2 className="text-lg font-bold text-txt">Alternatívne lieky</h2>
            <p className="text-xs text-txt3 mt-0.5">
              Náhrada za <span className="font-semibold">{drug.trade_name}</span>
            </p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-sm2 hover:bg-surface2 transition-colors text-txt2 hover:text-txt3"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="w-8 h-8 border-3 border-brand border-t-transparent rounded-full animate-spin" />
            </div>
          ) : data ? (
            <div className="space-y-4">
              {/* Current state */}
              <div className="bg-surface border border-bad/40 rounded-sm2 p-3">
                <div className="text-xs font-semibold text-bad uppercase tracking-wider mb-1">
                  Aktuálny stav
                </div>
                <div className="text-sm text-bad">
                  <span className="font-semibold">{drug.trade_name}</span> ({drug.active_substance})
                  má <span className="font-bold">{data.original_interaction_count}</span>{" "}
                  {data.original_interaction_count === 1 ? "interakciu" : "interakcií"} s ostatnými liekmi
                </div>
              </div>

              {data.suggestions.length > 0 ? (
                <>
                  <h3 className="text-xs font-semibold text-txt2 uppercase tracking-wider">
                    Navrhované alternatívy ({data.suggestions.length})
                  </h3>
                  <div className="space-y-2">
                    {data.suggestions.map((s, idx) => (
                      <div
                        key={idx}
                        className="bg-surface border border-ok/40 rounded-sm2 p-4"
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <div className="font-semibold text-txt text-sm">
                              {s.alternative.trade_name}
                            </div>
                            <div className="text-xs text-txt3 mt-0.5">
                              {s.alternative.active_substance}
                              {s.alternative.strength && ` &middot; ${s.alternative.strength}`}
                            </div>
                          </div>
                          <div className="bg-brand text-txt text-xs font-bold px-2.5 py-1 rounded-full">
                            -{s.interactions_avoided} interakcií
                          </div>
                        </div>
                        <p className="text-xs text-ok mt-2">{s.reason}</p>
                        {s.alternative.atc_code && (
                          <div className="text-[10px] text-txt2 mt-1">
                            ATC: {s.alternative.atc_code}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div className="text-center py-6">
                  <div className="w-12 h-12 bg-surface2 rounded-full flex items-center justify-center mx-auto mb-3">
                    <svg className="w-6 h-6 text-txt2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <p className="text-sm text-txt3 font-medium">Žiadne lepšie alternatívy</p>
                  <p className="text-xs text-txt2 mt-1">
                    V rovnakej ATC skupine nie sú lieky s menej interakciami.
                    Konzultujte s lekárom individuálne.
                  </p>
                </div>
              )}

              <div className="pt-3 border-t border-hairline text-[10px] text-txt2 text-center">
                Alternatívy sú navrhované na základe ATC klasifikácie a databázy interakcií.
                Vždy konzultujte zmenu liečby s ošetrujúcim lekárom.
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-txt3 text-sm">
              Nepodarilo sa načítať alternatívy.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
