import { useState, useEffect, useMemo } from "react";
import DrugSearch from "./components/DrugSearch";
import MedicationList from "./components/MedicationList";
import InteractionResults from "./components/InteractionResults";
import DrugDetailModal from "./components/DrugDetailModal";
import ATCBrowser from "./components/ATCBrowser";
import PatientProfiles from "./components/PatientProfiles";
import StatsPanel from "./components/StatsPanel";
import PharmacistChat from "./components/PharmacistChat";
import DispensingWindow from "./components/DispensingWindow";
import ImpactDashboard from "./components/ImpactDashboard";
import { checkInteractions, getStats } from "./api/client";

const TABS = [
  { id: "dispense", label: "Výdajové okno", icon: "counter" },
  { id: "pharmacist", label: "AI Lekárnik", icon: "chat" },
  { id: "checker", label: "Kontrola interakcií", icon: "shield" },
  { id: "atc", label: "ATC klasifikácia", icon: "grid" },
  { id: "profiles", label: "Profily pacientov", icon: "users" },
  { id: "impact", label: "Dopad", icon: "chart" },
];

// Tabs rendered as an operator console rather than a light web page.
const DARK_TABS = new Set(["dispense", "impact"]);

export default function App() {
  const [activeTab, setActiveTab] = useState("dispense");
  const [sessionResults, setSessionResults] = useState([]);
  const [medications, setMedications] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);
  const [selectedDrug, setSelectedDrug] = useState(null);

  const selectedIds = useMemo(
    () => new Set(medications.map((d) => d.id)),
    [medications]
  );

  useEffect(() => {
    getStats().then(setStats).catch(() => {});
  }, []);

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

  function handleLoadProfile(drugs) {
    setMedications(drugs);
    setResults(null);
    setError(null);
    setActiveTab("checker");
  }

  function handleDrugClick(drug) {
    setSelectedDrug(drug);
  }

  function handleAddFromBrowser(drug) {
    handleAdd(drug);
    setActiveTab("checker");
  }

  const dark = DARK_TABS.has(activeTab);

  return (
    <div className={`min-h-screen transition-colors ${dark ? "bg-slate-950" : "bg-slate-50"}`}>
      {/* Header */}
      <header
        className={`sticky top-0 z-40 border-b transition-colors ${
          dark ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200"
        }`}
      >
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center shadow-sm">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <div>
                <h1 className={`text-lg font-bold leading-tight ${dark ? "text-slate-50" : "text-slate-900"}`}>
                  AvatarAI <span className="font-normal text-slate-400">Dispense</span>
                </h1>
                <p className="text-[11px] text-slate-400 leading-tight">
                  Klinická inteligencia pre výdajné okno
                </p>
              </div>
            </div>

            {/* Stats badges */}
            {stats && (
              <div className="hidden md:flex items-center gap-4 text-xs">
                <div className="flex items-center gap-1.5 text-slate-500">
                  <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
                  <span>{stats.total_drugs.toLocaleString()} liekov</span>
                </div>
                <div className="text-slate-300">|</div>
                <div className="text-slate-500">
                  {stats.total_interactions.toLocaleString()} interakcií
                </div>
              </div>
            )}

            <div className="flex items-center gap-2">
              <span
                className={`text-[10px] px-2.5 py-1 rounded-full font-semibold border ${
                  dark
                    ? "bg-slate-800 text-slate-300 border-slate-700"
                    : "bg-gradient-to-r from-blue-50 to-indigo-50 text-blue-700 border-blue-100"
                }`}
              >
                Demo · pilot Dr.Max
              </span>
            </div>
          </div>

          {/* Navigation tabs */}
          <nav className="flex gap-1 -mb-px">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? dark
                      ? "border-cyan-400 text-cyan-300"
                      : "border-blue-600 text-blue-600"
                    : dark
                    ? "border-transparent text-slate-500 hover:text-slate-300 hover:border-slate-700"
                    : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
                }`}
              >
                <TabIcon icon={tab.icon} />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-6xl mx-auto px-4 py-6">
        {activeTab === "dispense" && (
          <DispensingWindow
            onSessionResult={(r) => setSessionResults((prev) => [...prev, r])}
          />
        )}

        {activeTab === "impact" && <ImpactDashboard sessionResults={sessionResults} />}

        {activeTab === "pharmacist" && <PharmacistChat />}

        {activeTab === "checker" && (
          <CheckerTab
            medications={medications}
            selectedIds={selectedIds}
            results={results}
            loading={loading}
            error={error}
            stats={stats}
            onAdd={handleAdd}
            onRemove={handleRemove}
            onCheck={handleCheck}
            onReset={handleReset}
            onDrugClick={handleDrugClick}
          />
        )}

        {activeTab === "atc" && (
          <ATCBrowser
            onAddDrug={handleAddFromBrowser}
            onDrugClick={handleDrugClick}
            selectedIds={selectedIds}
          />
        )}

        {activeTab === "profiles" && (
          <PatientProfiles
            currentMedications={medications}
            onLoadProfile={handleLoadProfile}
          />
        )}
      </main>

      {/* Drug detail modal */}
      {selectedDrug && (
        <DrugDetailModal
          drugId={selectedDrug.id}
          onClose={() => setSelectedDrug(null)}
          onAdd={(drug) => {
            handleAdd(drug);
            setSelectedDrug(null);
          }}
          isSelected={selectedIds.has(selectedDrug.id)}
        />
      )}

      {/* Footer */}
      <footer className={`border-t mt-16 ${dark ? "border-slate-800 bg-slate-950" : "border-slate-200 bg-white"}`}>
        <div className="max-w-6xl mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-xs text-slate-400">
              AvatarAI Dispense &mdash; funkčný prototyp pre slovenský lekárenský trh
            </p>
            <div className="flex items-center gap-4 text-xs text-slate-400">
              <span>Dáta: DDInter 2.0 + register ŠÚKL</span>
              <span className="text-slate-300">|</span>
              <span className="text-amber-500 font-medium">Nie je určený na klinické rozhodovanie</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

function CheckerTab({ medications, selectedIds, results, loading, error, stats, onAdd, onRemove, onCheck, onReset, onDrugClick }) {
  return (
    <div className="space-y-6">
      {!results ? (
        <>
          {/* Stats cards - only show when no meds selected */}
          {medications.length === 0 && stats && <StatsPanel stats={stats} />}

          {/* Search section */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-slate-900">
                {medications.length === 0 ? "Začnite vyhľadávaním lieku" : "Pridať ďalší liek"}
              </h2>
              <p className="text-sm text-slate-500 mt-0.5">
                Zadajte názov lieku alebo účinnej látky
              </p>
            </div>
            <DrugSearch onAdd={onAdd} selectedIds={selectedIds} onDrugClick={onDrugClick} />
          </div>

          {/* Medication list */}
          <MedicationList drugs={medications} onRemove={onRemove} onDrugClick={onDrugClick} />

          {/* Action bar */}
          {medications.length >= 2 && (
            <div className="flex items-center justify-between bg-white rounded-xl border border-slate-200 shadow-sm p-4">
              <div className="text-sm text-slate-600">
                <span className="font-semibold text-slate-900">{medications.length}</span> liekov vybraných &middot;{" "}
                <span className="font-semibold text-slate-900">{medications.length * (medications.length - 1) / 2}</span> párov na kontrolu
              </div>
              <button
                onClick={onCheck}
                disabled={loading}
                className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 disabled:from-blue-400 disabled:to-indigo-400 text-white font-semibold px-6 py-2.5 rounded-lg shadow-sm hover:shadow-md transition-all flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Kontrolujem...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                    Skontrolovať interakcie
                  </>
                )}
              </button>
            </div>
          )}

          {medications.length === 1 && (
            <p className="text-center text-sm text-slate-400 py-2">
              Pridajte aspoň 2 lieky pre kontrolu interakcií
            </p>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4 text-sm flex items-center gap-3">
              <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
              </svg>
              {error}
            </div>
          )}

          {/* Demo scenarios */}
          {medications.length === 0 && (
            <DemoScenarios onLoad={(meds) => {
              meds.forEach(onAdd);
            }} />
          )}
        </>
      ) : (
        <InteractionResults
          data={results}
          medications={medications}
          onReset={onReset}
          onDrugClick={onDrugClick}
        />
      )}
    </div>
  );
}

function DemoScenarios({ onLoad }) {
  const scenarios = [
    {
      title: "Starší pacient",
      subtitle: "Polyfarmácia",
      description: "Warfarin, Nurofen, Helicid, Simvacard, Hipres",
      icon: "elderly",
      drugs: [
        { id: 2152, trade_name: "WARFARIN ORION 5MG", active_substance: "warfarin", atc_code: "B01AA03" },
        { id: 6096, trade_name: "NUROFEN 400MG", active_substance: "ibuprofen", atc_code: "M01AE01" },
        { id: 480, trade_name: "HELICID 20MG", active_substance: "omeprazole", atc_code: "A02BC01" },
        { id: 10795, trade_name: "Simvacard 20 mg", active_substance: "simvastatin", atc_code: "C10AA01" },
        { id: 305, trade_name: "HIPRES 5MG", active_substance: "amlodipine", atc_code: "C08CA01" },
      ],
    },
    {
      title: "Depresia + Bolesť",
      subtitle: "Sérotonínový syndróm",
      description: "Zoloft, Tramal, Paralen, Voltaren",
      icon: "brain",
      drugs: [
        { id: 10588, trade_name: "ZOLOFT 50MG", active_substance: "sertraline", atc_code: "N06AB06" },
        { id: 4373, trade_name: "TRAMAL 100MG", active_substance: "tramadol", atc_code: "N02AX02" },
        { id: 7486, trade_name: "PARALEN 500MG", active_substance: "paracetamol", atc_code: "N02BE01" },
        { id: 5097, trade_name: "VOLTAREN ACTIGO EXTRA 25MG", active_substance: "diclofenac", atc_code: "M01AB05" },
      ],
    },
    {
      title: "Antibiotikum + Chronická liečba",
      subtitle: "CYP interakcie",
      description: "Ciprinol, Siofor, Warfarin",
      icon: "pill",
      drugs: [
        { id: 2157, trade_name: "CIPRINOL 250MG", active_substance: "ciprofloxacin hydrochloride", atc_code: "J01MA02" },
        { id: 4553, trade_name: "SIOFOR 850MG", active_substance: "metformin", atc_code: "A10BA02" },
        { id: 2152, trade_name: "WARFARIN ORION 5MG", active_substance: "warfarin", atc_code: "B01AA03" },
      ],
    },
  ];

  return (
    <div className="mt-8 pt-6 border-t border-slate-200">
      <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider text-center mb-4">
        Skúšobné scenáre
      </h3>
      <div className="grid gap-3 md:grid-cols-3">
        {scenarios.map((s) => (
          <button
            key={s.title}
            onClick={() => onLoad(s.drugs)}
            className="text-left bg-white border border-slate-200 rounded-xl p-4 hover:border-blue-300 hover:shadow-md transition-all group"
          >
            <div className="flex items-center gap-2 mb-2">
              <ScenarioIcon icon={s.icon} />
              <div>
                <span className="font-semibold text-slate-800 group-hover:text-blue-700 transition-colors text-sm">
                  {s.title}
                </span>
                <span className="text-[10px] bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full ml-2">
                  {s.subtitle}
                </span>
              </div>
            </div>
            <p className="text-xs text-slate-400">{s.description}</p>
            <div className="mt-2 text-[10px] text-blue-500 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
              Načítať scenár &rarr;
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

function TabIcon({ icon }) {
  if (icon === "counter") {
    return (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 21h18M4 21V10h16v11M8 10V6a4 4 0 118 0v4M9 15h6" />
      </svg>
    );
  }
  if (icon === "chart") {
    return (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 20h18M7 20v-7m5 7V7m5 13v-10" />
      </svg>
    );
  }
  if (icon === "chat") {
    return (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
      </svg>
    );
  }
  if (icon === "shield") {
    return (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    );
  }
  if (icon === "grid") {
    return (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
      </svg>
    );
  }
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
    </svg>
  );
}

function ScenarioIcon({ icon }) {
  if (icon === "elderly") {
    return (
      <div className="w-7 h-7 bg-amber-50 rounded-lg flex items-center justify-center">
        <svg className="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
        </svg>
      </div>
    );
  }
  if (icon === "brain") {
    return (
      <div className="w-7 h-7 bg-purple-50 rounded-lg flex items-center justify-center">
        <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
      </div>
    );
  }
  return (
    <div className="w-7 h-7 bg-blue-50 rounded-lg flex items-center justify-center">
      <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
      </svg>
    </div>
  );
}
