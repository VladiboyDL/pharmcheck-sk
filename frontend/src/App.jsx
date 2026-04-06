import { useState, useMemo } from "react";
import DrugSearch from "./components/DrugSearch";
import MedicationList from "./components/MedicationList";
import InteractionResults from "./components/InteractionResults";
import { checkInteractions } from "./api/client";

export default function App() {
  const [medications, setMedications] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const selectedIds = useMemo(
    () => new Set(medications.map((d) => d.id)),
    [medications]
  );

  function handleAdd(drug) {
    if (selectedIds.has(drug.id)) return;
    setMedications((prev) => [...prev, drug]);
    setResults(null);
    setError(null);
  }

  function handleRemove(id) {
    setMedications((prev) => prev.filter((d) => d.id !== id));
    setResults(null);
    setError(null);
  }

  async function handleCheck() {
    if (medications.length < 2) return;
    setLoading(true);
    setError(null);
    try {
      const data = await checkInteractions(medications.map((d) => d.id));
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setMedications([]);
    setResults(null);
    setError(null);
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hlavička */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-sm">
            <svg
              className="w-6 h-6 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
              />
            </svg>
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">PharmCheck SK</h1>
            <p className="text-xs text-gray-500">
              Kontrola liekových interakcií
            </p>
          </div>
          <div className="ml-auto">
            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full font-medium">
              POC v0.1
            </span>
          </div>
        </div>
      </header>

      {/* Hlavný obsah */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {!results ? (
          <div className="space-y-6">
            {/* Pokyny */}
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Kontrola liekových interakcií
              </h2>
              <p className="text-gray-500 max-w-lg mx-auto">
                Pridajte lieky pacienta a skontrolujte možné liekové interakcie.
                Systém skontroluje všetky kombinácie a zobrazí potenciálne
                riziká.
              </p>
            </div>

            {/* Vyhľadávanie */}
            <DrugSearch onAdd={handleAdd} selectedIds={selectedIds} />

            {/* Zoznam liekov */}
            <MedicationList drugs={medications} onRemove={handleRemove} />

            {/* Tlačidlo kontroly */}
            {medications.length >= 2 && (
              <div className="flex justify-center pt-4">
                <button
                  onClick={handleCheck}
                  disabled={loading}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold px-8 py-3 rounded-xl shadow-sm hover:shadow-md transition-all flex items-center gap-2"
                >
                  {loading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Kontrolujem...
                    </>
                  ) : (
                    <>
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                        />
                      </svg>
                      Skontrolovať interakcie
                    </>
                  )}
                </button>
              </div>
            )}

            {medications.length === 1 && (
              <p className="text-center text-sm text-gray-400">
                Pridajte aspoň 2 lieky pre kontrolu interakcií
              </p>
            )}

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4 text-sm">
                {error}
              </div>
            )}

            {/* Skúšobné scenáre */}
            {medications.length === 0 && (
              <div className="mt-12 pt-8 border-t border-gray-200">
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider text-center mb-4">
                  Skúšobné scenáre
                </h3>
                <div className="grid gap-3 md:grid-cols-3">
                  <DemoScenario
                    title="Starší pacient"
                    subtitle="Polyfarmácia"
                    drugs="Warfarin, Nurofen, Helicid, Simvacard, Norvasc"
                    onLoad={() => {
                      setMedications([
                        { id: 1, trade_name: "Warfarin Orion 5 mg", active_substance: "warfarin" },
                        { id: 63, trade_name: "Nurofen 400", active_substance: "ibuprofen" },
                        { id: 180, trade_name: "Helicid 20 mg", active_substance: "omeprazole" },
                        { id: 10, trade_name: "Simvacard 20 mg", active_substance: "simvastatin" },
                        { id: 28, trade_name: "Norvasc 5 mg", active_substance: "amlodipine" },
                      ]);
                    }}
                  />
                  <DemoScenario
                    title="Depresia + Bolesť"
                    subtitle="Serotonín"
                    drugs="Zoloft, Tramal, Paralen, Voltaren"
                    onLoad={() => {
                      setMedications([
                        { id: 113, trade_name: "Zoloft 50 mg", active_substance: "sertraline" },
                        { id: 74, trade_name: "Tramal 50 mg", active_substance: "tramadol" },
                        { id: 59, trade_name: "Paralen 500", active_substance: "paracetamol" },
                        { id: 68, trade_name: "Voltaren 50 mg", active_substance: "diclofenac" },
                      ]);
                    }}
                  />
                  <DemoScenario
                    title="Antibiotikum"
                    subtitle="Interakcie"
                    drugs="Ciprinol, Siofor, Warfarin"
                    onLoad={() => {
                      setMedications([
                        { id: 95, trade_name: "Ciprinol 500 mg", active_substance: "ciprofloxacin" },
                        { id: 158, trade_name: "Siofor 850 mg", active_substance: "metformin" },
                        { id: 1, trade_name: "Warfarin Orion 5 mg", active_substance: "warfarin" },
                      ]);
                    }}
                  />
                </div>
              </div>
            )}
          </div>
        ) : (
          <InteractionResults data={results} onReset={handleReset} />
        )}
      </main>

      {/* Päta */}
      <footer className="border-t border-gray-200 mt-16">
        <div className="max-w-4xl mx-auto px-4 py-6 text-center">
          <p className="text-xs text-gray-400">
            PharmCheck SK &mdash; Proof of Concept. Interakčné dáta: DDInter
            2.0. Tento nástroj nie je určený na klinické rozhodovanie.
          </p>
        </div>
      </footer>
    </div>
  );
}

function DemoScenario({ title, subtitle, drugs, onLoad }) {
  return (
    <button
      onClick={onLoad}
      className="text-left bg-white border border-gray-200 rounded-xl p-4 hover:border-blue-300 hover:shadow-md transition-all group"
    >
      <div className="flex items-center gap-2 mb-1">
        <span className="font-semibold text-gray-800 group-hover:text-blue-700 transition-colors">
          {title}
        </span>
        <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
          {subtitle}
        </span>
      </div>
      <p className="text-xs text-gray-400">{drugs}</p>
    </button>
  );
}
