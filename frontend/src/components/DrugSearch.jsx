import { useState, useRef, useEffect } from "react";
import { searchDrugs } from "../api/client";

export default function DrugSearch({ onAdd, selectedIds }) {
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
    }, 250);
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
          className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <input
          type="text"
          value={query}
          onChange={handleChange}
          placeholder="Vyhľadajte liek (napr. Paralen, Warfarin, Nurofen...)"
          className="w-full pl-12 pr-4 py-4 text-lg border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition-all bg-white shadow-sm"
        />
        {loading && (
          <div className="absolute right-4 top-1/2 -translate-y-1/2">
            <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>

      {isOpen && results.length > 0 && (
        <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-xl shadow-lg max-h-80 overflow-y-auto">
          {results.map((drug) => {
            const alreadyAdded = selectedIds.has(drug.id);
            return (
              <button
                key={drug.id}
                onClick={() => !alreadyAdded && handleSelect(drug)}
                disabled={alreadyAdded}
                className={`w-full text-left px-4 py-3 border-b border-gray-50 last:border-0 transition-colors ${
                  alreadyAdded
                    ? "bg-gray-50 text-gray-400 cursor-not-allowed"
                    : "hover:bg-blue-50 cursor-pointer"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-medium text-gray-900">
                      {drug.trade_name}
                    </span>
                    <span className="text-gray-500 ml-2 text-sm">
                      ({drug.active_substance})
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {drug.strength && (
                      <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                        {drug.strength}
                      </span>
                    )}
                    {alreadyAdded && (
                      <span className="text-xs text-green-600 font-medium">
                        Pridaný
                      </span>
                    )}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      )}

      {isOpen && query.length >= 2 && results.length === 0 && !loading && (
        <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-xl shadow-lg p-4 text-center text-gray-500">
          Žiadne výsledky pre &ldquo;{query}&rdquo;
        </div>
      )}
    </div>
  );
}
