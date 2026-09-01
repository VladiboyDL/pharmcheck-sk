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
      <section className="rounded-card border border-hairline bg-ink p-5">
        <div className="flex items-center gap-2 mb-4">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          <h2 className="text-sm font-semibold text-txt">Namerané v tejto relácii</h2>
          <span className="text-[10px] text-txt3">skutočné výstupy systému, nie odhad</span>
        </div>

        {measured.runs === 0 ? (
          <p className="text-xs text-txt3 py-6 text-center">
            Zatiaľ neprebehol žiadny výdaj. Prejdite na kartu „Výdajové okno“ a spustite kontrolu.
          </p>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-6 gap-px rounded-sm2 overflow-hidden bg-surface2">
            <Stat value={measured.runs} label="výdajov" />
            <Stat value={measured.checks.toLocaleString("sk-SK")} label="kontrol" />
            <Stat value={measured.pairs} label="liekových párov" />
            <Stat value={measured.criticals} label="kritických nálezov" tone="red" />
            <Stat value={measured.majors} label="závažných interakcií" tone="amber" />
            <Stat value={`${measured.avgMs} ms`} label="priemerný čas" />
          </div>
        )}

        {stats && (
          <div className="mt-4 pt-4 border-t border-hairline flex flex-wrap gap-x-6 gap-y-2 text-[11px] text-txt3">
            <span>
              Databáza: <span className="text-txt2 font-medium">{stats.total_drugs.toLocaleString("sk-SK")}</span> liekov
            </span>
            <span>
              <span className="text-txt2 font-medium">{stats.total_interactions.toLocaleString("sk-SK")}</span> interakčných záznamov
            </span>
            <span>
              z toho <span className="text-bad font-medium">{stats.severity_breakdown["Závažná"]?.toLocaleString("sk-SK")}</span> závažných
            </span>
            <span>Zdroj: DDInter 2.0 + ŠÚKL register</span>
          </div>
        )}
      </section>

      {/* ── Audit trail ─────────────────────────────────────────────────────── */}
      <section className="rounded-card border border-hairline bg-ink p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-txt">Auditný záznam výdajov</h2>
          <span className="text-[10px] text-txt3">append-only · reťazec opatrovníctva</span>
        </div>
        {log.length === 0 ? (
          <p className="text-xs text-txt3 py-4 text-center">Zatiaľ prázdny.</p>
        ) : (
          <div className="overflow-x-auto -mx-5 px-5">
            <table className="w-full text-xs min-w-[560px]">
              <thead>
                <tr className="text-left text-txt3 border-b border-hairline">
                  <th className="pb-2 font-medium">ID záznamu</th>
                  <th className="pb-2 font-medium">Čas</th>
                  <th className="pb-2 font-medium">Pacient</th>
                  <th className="pb-2 font-medium text-right">Kontrol</th>
                  <th className="pb-2 font-medium text-right">Rozhodnutie</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-hairline">
                {log.map((e) => (
                  <tr key={e.audit_id}>
                    <td className="py-2 font-mono text-txt2">{e.audit_id}</td>
                    <td className="py-2 text-txt3 tabular">{e.timestamp.replace("T", " ")}</td>
                    <td className="py-2 text-txt2">{e.patient || "—"}</td>
                    <td className="py-2 text-right text-txt2 tabular">{e.checks_run}</td>
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
      <section className="rounded-card border border-hairline bg-ink p-5">
        <div className="flex items-center gap-2 mb-1">
          <span className="w-1.5 h-1.5 rounded-full bg-warn" />
          <h2 className="text-sm font-semibold text-txt">Modelovaný dopad pri nasadení</h2>
        </div>
        <p className="text-[11px] text-txt3 mb-4">
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
          <summary className="text-[11px] text-txt3 cursor-pointer hover:text-txt2 select-none">
            Predpoklady modelu
          </summary>
          <ul className="mt-2 space-y-1 text-[11px] text-txt3 pl-4 list-disc marker:text-txt3">
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
    live: ["border-ok/70 bg-ok/10", "text-ok", "bg-emerald-400"],
    simulated: ["border-warn/40 bg-warn/10", "text-warn", "bg-warn"],
    pilot: ["border-hairline bg-surface", "text-txt2", "bg-slate-600"],
  };

  return (
    <section className="rounded-card border border-hairline bg-ink p-5">
      <h2 className="text-sm font-semibold text-txt">Stav platformy</h2>
      <p className="text-[11px] text-txt3 mt-0.5 mb-4">
        Čo je postavené, čo je v deme simulované a čo prináša pilot — bez prikrášľovania.
      </p>

      <div className="grid gap-3 md:grid-cols-3">
        {MATURITY.map((col) => {
          const [box, text, dot] = tone[col.stage];
          return (
            <div key={col.stage} className={`rounded-sm2 border p-4 ${box}`}>
              <div className="flex items-center gap-2">
                <span className={`w-1.5 h-1.5 rounded-full ${dot}`} />
                <h3 className={`text-xs font-semibold ${text}`}>{col.title}</h3>
              </div>
              <p className="text-[10px] text-txt3 mt-1 mb-2.5">{col.detail}</p>
              <ul className="space-y-1.5">
                {col.items.map((i) => (
                  <li key={i} className="text-[11px] text-txt2 leading-snug flex gap-1.5">
                    <span className="text-txt3 flex-shrink-0">—</span>
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
    DISPENSE: ["bg-ok/15 text-ok", "VYDAŤ"],
    CONSULT: ["bg-warn/15 text-warn", "KONZULTOVAŤ"],
    BLOCK: ["bg-bad/15 text-bad", "NEVYDAŤ"],
  };
  const [cls, label] = map[verdict] ?? ["bg-surface2 text-txt2", verdict];
  return <span className={`rounded px-2 py-0.5 text-[10px] font-semibold ${cls}`}>{label}</span>;
}

function Stat({ value, label, tone }) {
  const colour = tone === "red" ? "text-bad" : tone === "amber" ? "text-warn" : "text-txt";
  return (
    <div className="bg-ink px-3 py-3 text-center">
      <p className={`text-xl font-mono tabular leading-none ${colour}`}>{value}</p>
      <p className="text-[10px] text-txt3 mt-1">{label}</p>
    </div>
  );
}

function BigStat({ value, label, detail, tone }) {
  const ring =
    tone === "emerald"
      ? "border-ok/70 bg-ok/10"
      : tone === "cyan"
      ? "border-brand/40 bg-brand/10"
      : "border-hairline bg-surface";
  const text = tone === "emerald" ? "text-ok" : tone === "cyan" ? "text-brand" : "text-txt";
  return (
    <div className={`rounded-sm2 border p-4 ${ring}`}>
      <p className={`text-3xl font-mono tabular ${text}`}>{value}</p>
      <p className="text-xs text-txt2 mt-1">{label}</p>
      <p className="text-[10px] text-txt3 mt-1.5 leading-relaxed">{detail}</p>
    </div>
  );
}

function Input({ label, value, onChange, min, max, step }) {
  return (
    <label className="block">
      <span className="text-[10px] font-mono uppercase tracking-[0.14em] text-txt3">{label}</span>
      <input
        type="number"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(e) => onChange(Math.max(min, Math.min(max, Number(e.target.value) || min)))}
        className="mt-1 w-full rounded-sm2 bg-panel border border-hairline focus:border-brand focus:outline-none text-txt text-sm tabular px-3 py-2"
      />
    </label>
  );
}
