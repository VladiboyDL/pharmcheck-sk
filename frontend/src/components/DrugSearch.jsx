import { useState, useRef, useEffect } from "react";
import { searchDrugs } from "../api/client";

export default function DrugSearch({ onAdd, selectedIds, onDrugClick }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const wrapperRef = useRef(null);
  const debounceRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(e) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function handleChange(e) {
    const val = e.target.value;
    setQuery(val);

    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (val.length < 2) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const data = await searchDrugs(val);
        setResults(data.results);
        setIsOpen(true);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 200);
  }

  function handleSelect(drug) {
    onAdd(drug);
    setQuery("");
    setResults([]);
    setIsOpen(false);
  }

  return (
    <div ref={wrapperRef} className="relative">
      <div className="relative">
        <svg
          className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400"
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          type="text"
          value={query}
          onChange={handleChange}
          placeholder="Vyhľadajte liek (napr. Paralen, Warfarin, Nurofen...)"
          className="w-full pl-12 pr-4 py-3.5 text-base border border-slate-200 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none transition-all bg-white"
        />
        {loading && (
          <div className="absolute right-4 top-1/2 -translate-y-1/2">
            <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>

      {isOpen && results.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-slate-200 rounded-xl shadow-lg max-h-80 overflow-y-auto">
          {results.map((drug) => {
            const alreadyAdded = selectedIds.has(drug.id);
            return (
              <div
                key={drug.id}
                className={`flex items-center justify-between px-4 py-2.5 border-b border-slate-50 last:border-0 transition-colors ${
                  alreadyAdded ? "bg-slate-50" : "hover:bg-blue-50 cursor-pointer"
                }`}
              >
                <button
                  onClick={() => !alreadyAdded && handleSelect(drug)}
                  disabled={alreadyAdded}
                  className="flex-1 text-left"
                >
                  <span className="font-medium text-slate-900 text-sm">{drug.trade_name}</span>
                  <span className="text-slate-400 ml-2 text-xs">({drug.active_substance})</span>
                </button>
                <div className="flex items-center gap-2 flex-shrink-0">
                  {drug.strength && (
                    <span className="text-[10px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded">
                      {drug.strength}
                    </span>
                  )}
                  {drug.atc_code && (
                    <span className="text-[10px] bg-blue-50 text-blue-500 px-1.5 py-0.5 rounded">
                      {drug.atc_code}
                    </span>
                  )}
                  {alreadyAdded ? (
                    <span className="text-[10px] text-green-600 font-medium">Pridaný</span>
                  ) : (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDrugClick?.(drug);
                      }}
                      className="text-[10px] text-slate-400 hover:text-blue-600 transition-colors"
                      title="Detail"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {isOpen && query.length >= 2 && results.length === 0 && !loading && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-slate-200 rounded-xl shadow-lg p-4 text-center text-slate-500 text-sm">
          Žiadne výsledky pre &ldquo;{query}&rdquo;
        </div>
      )}
    </div>
  );
}
