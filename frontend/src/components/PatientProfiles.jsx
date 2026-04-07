import { useState, useEffect } from "react";

const STORAGE_KEY = "pharmcheck_profiles";

function loadProfiles() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveProfiles(profiles) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(profiles));
}

export default function PatientProfiles({ currentMedications, onLoadProfile }) {
  const [profiles, setProfiles] = useState(loadProfiles);
  const [showSave, setShowSave] = useState(false);
  const [newName, setNewName] = useState("");
  const [newNote, setNewNote] = useState("");

  useEffect(() => {
    saveProfiles(profiles);
  }, [profiles]);

  function handleSave() {
    if (!newName.trim() || currentMedications.length === 0) return;
    const profile = {
      id: Date.now().toString(),
      name: newName.trim(),
      note: newNote.trim(),
      medications: currentMedications,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    setProfiles((prev) => [profile, ...prev]);
    setNewName("");
    setNewNote("");
    setShowSave(false);
  }

  function handleDelete(id) {
    setProfiles((prev) => prev.filter((p) => p.id !== id));
  }

  function handleUpdate(id) {
    setProfiles((prev) =>
      prev.map((p) =>
        p.id === id
          ? { ...p, medications: currentMedications, updatedAt: new Date().toISOString() }
          : p
      )
    );
  }

  return (
    <div className="space-y-6">
      {/* Save current */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Profily pacientov</h2>
            <p className="text-sm text-slate-500 mt-0.5">
              Uložte a spravujte zoznamy liekov pre svojich pacientov
            </p>
          </div>
          {currentMedications.length > 0 && !showSave && (
            <button
              onClick={() => setShowSave(true)}
              className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Uložiť aktuálne lieky
            </button>
          )}
        </div>

        {showSave && (
          <div className="bg-slate-50 rounded-lg p-4 space-y-3">
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Meno pacienta alebo označenie"
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-200 outline-none"
              autoFocus
            />
            <input
              type="text"
              value={newNote}
              onChange={(e) => setNewNote(e.target.value)}
              placeholder="Poznámka (voliteľné)"
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-200 outline-none"
            />
            <div className="text-xs text-slate-500">
              {currentMedications.length} liekov: {currentMedications.map((m) => m.trade_name).join(", ")}
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleSave}
                disabled={!newName.trim()}
                className="bg-blue-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-slate-300 transition-colors"
              >
                Uložiť profil
              </button>
              <button
                onClick={() => setShowSave(false)}
                className="text-sm text-slate-500 px-4 py-2 hover:text-slate-700"
              >
                Zrušiť
              </button>
            </div>
          </div>
        )}

        {currentMedications.length === 0 && !showSave && (
          <div className="bg-slate-50 rounded-lg p-4 text-sm text-slate-500 text-center">
            Pridajte lieky v záložke "Kontrola interakcií" a potom ich tu uložte ako profil pacienta.
          </div>
        )}
      </div>

      {/* Saved profiles */}
      {profiles.length > 0 ? (
        <div className="space-y-3">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Uložené profily ({profiles.length})
          </h3>
          {profiles.map((profile) => (
            <div
              key={profile.id}
              className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-gradient-to-br from-indigo-100 to-blue-100 rounded-lg flex items-center justify-center">
                      <svg className="w-4 h-4 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    </div>
                    <div>
                      <h4 className="font-semibold text-slate-900 text-sm">{profile.name}</h4>
                      {profile.note && (
                        <p className="text-xs text-slate-400">{profile.note}</p>
                      )}
                    </div>
                  </div>

                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {profile.medications.map((med) => (
                      <span
                        key={med.id}
                        className="text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded-md"
                      >
                        {med.trade_name}
                      </span>
                    ))}
                  </div>

                  <div className="mt-2 text-[10px] text-slate-400">
                    Vytvorené: {new Date(profile.createdAt).toLocaleDateString("sk-SK")}
                    {profile.updatedAt !== profile.createdAt && (
                      <> &middot; Aktualizované: {new Date(profile.updatedAt).toLocaleDateString("sk-SK")}</>
                    )}
                  </div>
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-slate-100 flex gap-2">
                <button
                  onClick={() => onLoadProfile(profile.medications)}
                  className="text-xs font-medium text-blue-600 hover:text-blue-800 px-3 py-1.5 rounded-lg hover:bg-blue-50 transition-colors"
                >
                  Načítať a skontrolovať
                </button>
                {currentMedications.length > 0 && (
                  <button
                    onClick={() => handleUpdate(profile.id)}
                    className="text-xs font-medium text-slate-500 hover:text-slate-700 px-3 py-1.5 rounded-lg hover:bg-slate-50 transition-colors"
                  >
                    Aktualizovať lieky
                  </button>
                )}
                <button
                  onClick={() => handleDelete(profile.id)}
                  className="text-xs font-medium text-red-500 hover:text-red-700 px-3 py-1.5 rounded-lg hover:bg-red-50 transition-colors ml-auto"
                >
                  Vymazať
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-slate-400 text-sm">
          Zatiaľ nemáte uložené žiadne profily.
        </div>
      )}
    </div>
  );
}
