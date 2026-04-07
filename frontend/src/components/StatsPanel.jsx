export default function StatsPanel({ stats }) {
  if (!stats) return null;

  const cards = [
    {
      label: "Liekov v databáze",
      value: stats.total_drugs.toLocaleString(),
      icon: "pill",
      color: "blue",
    },
    {
      label: "Známych interakcií",
      value: stats.total_interactions.toLocaleString(),
      icon: "warning",
      color: "amber",
    },
    {
      label: "Látok s interakciami",
      value: stats.drugs_with_interactions.toLocaleString(),
      icon: "link",
      color: "red",
    },
    {
      label: "ATC skupín",
      value: stats.top_atc_groups?.length || 0,
      icon: "grid",
      color: "indigo",
    },
  ];

  const colorMap = {
    blue: "from-blue-500 to-blue-600 shadow-blue-200",
    amber: "from-amber-500 to-amber-600 shadow-amber-200",
    red: "from-red-500 to-red-600 shadow-red-200",
    indigo: "from-indigo-500 to-indigo-600 shadow-indigo-200",
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {cards.map((card) => (
        <div
          key={card.label}
          className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm"
        >
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${colorMap[card.color]} shadow-sm flex items-center justify-center`}>
              <StatIcon icon={card.icon} />
            </div>
            <div>
              <div className="text-xl font-bold text-slate-900">{card.value}</div>
              <div className="text-[11px] text-slate-500 leading-tight">{card.label}</div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function StatIcon({ icon }) {
  if (icon === "pill") {
    return (
      <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
      </svg>
    );
  }
  if (icon === "warning") {
    return (
      <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
        <path d="M12 2L1 21h22L12 2zm0 3.83L19.53 19H4.47L12 5.83zM11 16h2v2h-2v-2zm0-6h2v4h-2v-4z" />
      </svg>
    );
  }
  if (icon === "link") {
    return (
      <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
      </svg>
    );
  }
  return (
    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6z" />
    </svg>
  );
}
