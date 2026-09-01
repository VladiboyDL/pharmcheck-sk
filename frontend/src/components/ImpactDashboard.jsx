import { useEffect, useMemo, useState } from "react";
import { getDispenseLog, getStats } from "../api/client";

/**
 * Two halves, deliberately separated:
 *   MEASURED  — what this system actually did in this session (audit log, live DB).
 *   MODELLED  — the business case, with every assumption exposed and editable.
 */
export default function ImpactDashboard({ sessionResults = [] }) {
  const [log, setLog] = useState([]);
  const [stats, setStats] = useState(null);

  const [branches, setBranches] = useState(3200);
  const [rxPerDay, setRxPerDay] = useState(200);
  const [pharmacists, setPharmacists] = useState(3);
  const [salary, setSalary] = useState(2400);

  useEffect(() => {
    getDispenseLog(20).then((d) => setLog(d.entries)).catch(() => {});
    getStats().then(setStats).catch(() => {});
  }, [sessionResults.length]);

  const measured = useMemo(() => {
    const checks = sessionResults.reduce((a, r) => a + r.summary.checks_run, 0);
    const pairs = sessionResults.reduce((a, r) => a + r.summary.pairs_checked, 0);
    const criticals = sessionResults.reduce((a, r) => a + r.summary.critical, 0);
    const majors = sessionResults.reduce((a, r) => a + r.summary.major_interactions, 0);
    const blocked = sessionResults.filter((r) => r.verdict === "BLOCK").length;
    const ms = sessionResults.reduce((a, r) => a + r.summary.duration_ms, 0);
    return {
      runs: sessionResults.length,
      checks,
      pairs,
      criticals,
      majors,
      blocked,
      avgMs: sessionResults.length ? (ms / sessionResults.length).toFixed(1) : 0,
    };
  }, [sessionResults]);

  // ── Model ────────────────────────────────────────────────────────────────
  // Conservative: one pharmacist retained per site, the rest is the delta.
  const staffSavedPerSite = Math.max(0, pharmacists - 1);
  const annualSalaryCost = salary * 12 * 1.352; // employer contributions, SK ~35.2%
  const savingsPerSite = staffSavedPerSite * annualSalaryCost;
  const totalSavings = savingsPerSite * branches;
  const rxPerYear = rxPerDay * 300 * branches;
  // 6.5 pairs on an average 4-item prescription
  const pairsPerYear = rxPerYear * 6.5;

  return (
    <div className="space-y-5">
      {/* ── Measured ────────────────────────────────────────────────────────── */}
      <section className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
        <div className="flex items-center gap-2 mb-4">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          <h2 className="text-sm font-semibold text-slate-100">Namerané v tejto relácii</h2>
          <span className="text-[10px] text-slate-600">skutočné výstupy systému, nie odhad</span>
        </div>

        {measured.runs === 0 ? (
          <p className="text-xs text-slate-500 py-6 text-center">
            Zatiaľ neprebehol žiadny výdaj. Prejdite na kartu „Výdajové okno“ a spustite kontrolu.
          </p>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-6 gap-px rounded-xl overflow-hidden bg-slate-800/60">
            <Stat value={measured.runs} label="výdajov" />
            <Stat value={measured.checks.toLocaleString("sk-SK")} label="kontrol" />
            <Stat value={measured.pairs} label="liekových párov" />
            <Stat value={measured.criticals} label="kritických nálezov" tone="red" />
            <Stat value={measured.majors} label="závažných interakcií" tone="amber" />
            <Stat value={`${measured.avgMs} ms`} label="priemerný čas" />
          </div>
        )}

        {stats && (
          <div className="mt-4 pt-4 border-t border-slate-800 flex flex-wrap gap-x-6 gap-y-2 text-[11px] text-slate-500">
            <span>
              Databáza: <span className="text-slate-300 font-medium">{stats.total_drugs.toLocaleString("sk-SK")}</span> liekov
            </span>
            <span>
              <span className="text-slate-300 font-medium">{stats.total_interactions.toLocaleString("sk-SK")}</span> interakčných záznamov
            </span>
            <span>
              z toho <span className="text-red-400 font-medium">{stats.severity_breakdown["Závažná"]?.toLocaleString("sk-SK")}</span> závažných
            </span>
            <span>Zdroj: DDInter 2.0 + ŠÚKL register</span>
          </div>
        )}
      </section>

      {/* ── Audit trail ─────────────────────────────────────────────────────── */}
      <section className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-slate-100">Auditný záznam výdajov</h2>
          <span className="text-[10px] text-slate-600">append-only · reťazec opatrovníctva</span>
        </div>
        {log.length === 0 ? (
          <p className="text-xs text-slate-500 py-4 text-center">Zatiaľ prázdny.</p>
        ) : (
          <div className="overflow-x-auto -mx-5 px-5">
            <table className="w-full text-xs min-w-[560px]">
              <thead>
                <tr className="text-left text-slate-500 border-b border-slate-800">
                  <th className="pb-2 font-medium">ID záznamu</th>
                  <th className="pb-2 font-medium">Čas</th>
                  <th className="pb-2 font-medium">Pacient</th>
                  <th className="pb-2 font-medium text-right">Kontrol</th>
                  <th className="pb-2 font-medium text-right">Rozhodnutie</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70">
                {log.map((e) => (
                  <tr key={e.audit_id}>
                    <td className="py-2 font-mono text-slate-400">{e.audit_id}</td>
                    <td className="py-2 text-slate-500 tabular-nums">{e.timestamp.replace("T", " ")}</td>
                    <td className="py-2 text-slate-300">{e.patient || "—"}</td>
                    <td className="py-2 text-right text-slate-400 tabular-nums">{e.checks_run}</td>
                    <td className="py-2 text-right">
                      <VerdictChip verdict={e.verdict} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* ── Modelled ────────────────────────────────────────────────────────── */}
      <section className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
        <div className="flex items-center gap-2 mb-1">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
          <h2 className="text-sm font-semibold text-slate-100">Modelovaný dopad pri nasadení</h2>
        </div>
        <p className="text-[11px] text-slate-500 mb-4">
          Projekcia, nie nameraná hodnota. Všetky vstupy sú upraviteľné — čísla sa prepočítajú okamžite.
        </p>

        <div className="grid gap-4 md:grid-cols-4 mb-5">
          <Input label="Pobočiek" value={branches} onChange={setBranches} min={1} max={5000} step={50} />
          <Input label="Receptov / deň / pobočku" value={rxPerDay} onChange={setRxPerDay} min={20} max={500} step={10} />
          <Input label="Farmaceutov / pobočku dnes" value={pharmacists} onChange={setPharmacists} min={1} max={8} step={1} />
          <Input label="Hrubá mzda / mesiac (€)" value={salary} onChange={setSalary} min={1000} max={5000} step={100} />
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <BigStat
            value={`${(totalSavings / 1_000_000).toFixed(1)} mil. €`}
            label="ročná úspora miezd"
            detail={`${staffSavedPerSite} FTE na pobočku × ${branches.toLocaleString("sk-SK")} pobočiek, vrátane odvodov 35,2 %`}
            tone="emerald"
          />
          <BigStat
            value={(pairsPerYear / 1_000_000).toFixed(0) + " mil."}
            label="liekových párov skontrolovaných ročne"
            detail={`${rxPerYear.toLocaleString("sk-SK")} receptov × 6,5 páru na recept — dnes sa nekontrolujú`}
            tone="cyan"
          />
          <BigStat
            value={`${((savingsPerSite / 1000)).toFixed(0)} tis. €`}
            label="úspora na jednu pobočku ročne"
            detail="Základ pre návratnosť pilotu na 5–10 slovenských lokalitách"
            tone="slate"
          />
        </div>

        <details className="mt-4 group">
          <summary className="text-[11px] text-slate-500 cursor-pointer hover:text-slate-300 select-none">
            Predpoklady modelu
          </summary>
          <ul className="mt-2 space-y-1 text-[11px] text-slate-500 pl-4 list-disc marker:text-slate-700">
            <li>Na každej pobočke zostáva jeden vyškolený pracovník — model počíta úsporu len nad tento základ.</li>
            <li>Odvody zamestnávateľa 35,2 % podľa slovenskej legislatívy.</li>
            <li>300 prevádzkových dní v roku.</li>
            <li>Priemerne 4 položky na recept, čo zodpovedá 6 až 7 liekovým párom na kontrolu.</li>
            <li>
              Model nezahŕňa úsporu zo zásob ani z prevencie liekových chýb — tie sú v obchodnom
              prípade uvedené samostatne a vyžadujú dáta z pilotu.
            </li>
          </ul>
        </details>
      </section>

      <Maturity />
    </div>
  );
}

/** What the exec will ask: how much of the one-pager actually exists today. */
const MATURITY = [
  {
    stage: "live",
    title: "Funguje dnes",
    detail: "Beží v tomto deme na reálnych dátach, bez simulácie.",
    items: [
      "Interakčný engine nad 160 295 záznamami a 10 824 prípravkami registra",
      "Validácia dávkovania — renálna funkcia, vek, gravidita, maximálne denné dávky",
      "Detekcia duplicitnej terapie naprieč 9 terapeutickými triedami",
      "Parsovanie eReceptu vrátane výpočtu dennej dávky zo zápisu 1-0-1",
      "Rozhodnutie o výdaji s auditným záznamom",
      "AI lekárnik — konverzačné vysvetlenie pre pacienta po slovensky",
    ],
  },
  {
    stage: "simulated",
    title: "Simulované v deme",
    detail: "Rozhranie je hotové, chýba napojenie na cudzí systém.",
    items: [
      "Načítanie karty poistenca — čaká na prístup do eZdravie / NCZI",
      "Biometrické overenie tváre — čaká na referenčné fotografie poisťovní",
      "Príjem eReceptu — dnes textom, produkčne cez rozhranie NCZI",
    ],
  },
  {
    stage: "pilot",
    title: "Predmet pilotu",
    detail: "Vyžaduje 5–10 lokalít a prevádzkové dáta Dr.Max.",
    items: [
      "Prediktívne zásoby a automatické dopĺňanie zo skladu",
      "Robotický výdaj a zabezpečený inventár kontrolovaných látok",
      "Integrácia na lekárenský a skladový systém Dr.Max",
      "Meranie reálneho dopadu na bezpečnosť, priepustnosť a personál",
    ],
  },
];

function Maturity() {
  const tone = {
    live: ["border-emerald-900/70 bg-emerald-950/20", "text-emerald-300", "bg-emerald-400"],
    simulated: ["border-amber-900/70 bg-amber-950/15", "text-amber-300", "bg-amber-400"],
    pilot: ["border-slate-800 bg-slate-900/40", "text-slate-400", "bg-slate-600"],
  };

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
      <h2 className="text-sm font-semibold text-slate-100">Stav platformy</h2>
      <p className="text-[11px] text-slate-500 mt-0.5 mb-4">
        Čo je postavené, čo je v deme simulované a čo prináša pilot — bez prikrášľovania.
      </p>

      <div className="grid gap-3 md:grid-cols-3">
        {MATURITY.map((col) => {
          const [box, text, dot] = tone[col.stage];
          return (
            <div key={col.stage} className={`rounded-xl border p-4 ${box}`}>
              <div className="flex items-center gap-2">
                <span className={`w-1.5 h-1.5 rounded-full ${dot}`} />
                <h3 className={`text-xs font-semibold ${text}`}>{col.title}</h3>
              </div>
              <p className="text-[10px] text-slate-500 mt-1 mb-2.5">{col.detail}</p>
              <ul className="space-y-1.5">
                {col.items.map((i) => (
                  <li key={i} className="text-[11px] text-slate-400 leading-snug flex gap-1.5">
                    <span className="text-slate-700 flex-shrink-0">—</span>
                    <span>{i}</span>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function VerdictChip({ verdict }) {
  const map = {
    DISPENSE: ["bg-emerald-500/15 text-emerald-300", "VYDAŤ"],
    CONSULT: ["bg-amber-500/15 text-amber-300", "KONZULTOVAŤ"],
    BLOCK: ["bg-red-500/15 text-red-300", "NEVYDAŤ"],
  };
  const [cls, label] = map[verdict] ?? ["bg-slate-800 text-slate-400", verdict];
  return <span className={`rounded px-2 py-0.5 text-[10px] font-semibold ${cls}`}>{label}</span>;
}

function Stat({ value, label, tone }) {
  const colour = tone === "red" ? "text-red-300" : tone === "amber" ? "text-amber-300" : "text-slate-100";
  return (
    <div className="bg-slate-950 px-3 py-3 text-center">
      <p className={`text-lg font-bold tabular-nums leading-none ${colour}`}>{value}</p>
      <p className="text-[10px] text-slate-500 mt-1">{label}</p>
    </div>
  );
}

function BigStat({ value, label, detail, tone }) {
  const ring =
    tone === "emerald"
      ? "border-emerald-900/70 bg-emerald-950/25"
      : tone === "cyan"
      ? "border-cyan-900/70 bg-cyan-950/25"
      : "border-slate-800 bg-slate-900/40";
  const text = tone === "emerald" ? "text-emerald-300" : tone === "cyan" ? "text-cyan-300" : "text-slate-200";
  return (
    <div className={`rounded-xl border p-4 ${ring}`}>
      <p className={`text-2xl font-bold tabular-nums ${text}`}>{value}</p>
      <p className="text-xs text-slate-300 mt-1">{label}</p>
      <p className="text-[10px] text-slate-500 mt-1.5 leading-relaxed">{detail}</p>
    </div>
  );
}

function Input({ label, value, onChange, min, max, step }) {
  return (
    <label className="block">
      <span className="text-[10px] uppercase tracking-wider text-slate-500">{label}</span>
      <input
        type="number"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(e) => onChange(Math.max(min, Math.min(max, Number(e.target.value) || min)))}
        className="mt-1 w-full rounded-lg bg-slate-900 border border-slate-800 focus:border-cyan-700 focus:outline-none text-slate-200 text-sm tabular-nums px-3 py-2"
      />
    </label>
  );
}
