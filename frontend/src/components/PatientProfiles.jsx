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
      <div className="bg-panel rounded-sm2 border border-hairline p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-txt">Profily pacientov</h2>
            <p className="text-sm text-txt3 mt-0.5">
              Uložte a spravujte zoznamy liekov pre svojich pacientov
            </p>
          </div>
          {currentMedications.length > 0 && !showSave && (
            <button
              onClick={() => setShowSave(true)}
              className="bg-brand text-txt text-sm font-semibold px-4 py-2 rounded-sm2 hover:bg-brandDeep transition-all flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Uložiť aktuálne lieky
            </button>
          )}
        </div>

        {showSave && (
          <div className="bg-ink rounded-sm2 p-4 space-y-3">
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Meno pacienta alebo označenie"
              className="w-full px-3 py-2 border border-hairline rounded-sm2 text-sm focus:border-brand focus:ring-1 focus:ring-brand outline-none"
              autoFocus
            />
            <input
              type="text"
              value={newNote}
              onChange={(e) => setNewNote(e.target.value)}
              placeholder="Poznámka (voliteľné)"
              className="w-full px-3 py-2 border border-hairline rounded-sm2 text-sm focus:border-brand focus:ring-1 focus:ring-brand outline-none"
            />
            <div className="text-xs text-txt3">
              {currentMedications.length} liekov: {currentMedications.map((m) => m.trade_name).join(", ")}
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleSave}
                disabled={!newName.trim()}
                className="bg-brand text-txt text-sm font-medium px-4 py-2 rounded-sm2 hover:bg-brand disabled:bg-surface2 transition-colors"
              >
                Uložiť profil
              </button>
              <button
                onClick={() => setShowSave(false)}
                className="text-sm text-txt3 px-4 py-2 hover:text-txt3"
              >
                Zrušiť
              </button>
            </div>
          </div>
        )}

        {currentMedications.length === 0 && !showSave && (
          <div className="bg-ink rounded-sm2 p-4 text-sm text-txt3 text-center">
            Pridajte lieky v záložke "Kontrola interakcií" a potom ich tu uložte ako profil pacienta.
          </div>
        )}
      </div>

      {/* Saved profiles */}
      {profiles.length > 0 ? (
        <div className="space-y-3">
          <h3 className="text-xs font-semibold text-txt2 uppercase tracking-wider">
            Uložené profily ({profiles.length})
          </h3>
          {profiles.map((profile) => (
            <div
              key={profile.id}
              className="bg-panel rounded-sm2 border border-hairline p-4 hover: transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-brand/15 rounded-sm2 flex items-center justify-center">
                      <svg className="w-4 h-4 text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    </div>
                    <div>
                      <h4 className="font-semibold text-txt text-sm">{profile.name}</h4>
                      {profile.note && (
                        <p className="text-xs text-txt2">{profile.note}</p>
                      )}
                    </div>
                  </div>

                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {profile.medications.map((med) => (
                      <span
                        key={med.id}
                        className="text-xs bg-surface2 text-txt3 px-2 py-1 rounded-md"
                      >
                        {med.trade_name}
                      </span>
                    ))}
                  </div>

                  <div className="mt-2 text-[10px] text-txt2">
                    Vytvorené: {new Date(profile.createdAt).toLocaleDateString("sk-SK")}
                    {profile.updatedAt !== profile.createdAt && (
                      <> &middot; Aktualizované: {new Date(profile.updatedAt).toLocaleDateString("sk-SK")}</>
                    )}
                  </div>
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-hairline flex gap-2">
                <button
                  onClick={() => onLoadProfile(profile.medications)}
                  className="text-xs font-medium text-brand hover:text-brand px-3 py-1.5 rounded-sm2 hover:bg-brand transition-colors"
                >
                  Načítať a skontrolovať
                </button>
                {currentMedications.length > 0 && (
                  <button
                    onClick={() => handleUpdate(profile.id)}
                    className="text-xs font-medium text-txt3 hover:text-txt3 px-3 py-1.5 rounded-sm2 hover:bg-ink transition-colors"
                  >
                    Aktualizovať lieky
                  </button>
                )}
                <button
                  onClick={() => handleDelete(profile.id)}
                  className="text-xs font-medium text-bad hover:text-bad px-3 py-1.5 rounded-sm2 hover:bg-surface transition-colors ml-auto"
                >
                  Vymazať
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-txt2 text-sm">
          Zatiaľ nemáte uložené žiadne profily.
        </div>
      )}
    </div>
  );
}
