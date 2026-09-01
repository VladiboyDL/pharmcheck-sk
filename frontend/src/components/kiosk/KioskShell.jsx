/**
 * Chrome shared by every kiosk screen: one message at a time, a calm progress rail,
 * and nothing else competing for attention.
 */
export function Screen({ children, footer }) {
  return (
    <div className="min-h-[34rem] flex flex-col">
      <div className="flex-1 flex flex-col justify-center">{children}</div>
      {footer && <div className="pt-6">{footer}</div>}
    </div>
  );
}

export function Title({ children, sub }) {
  return (
    <div className="text-center">
      <h2 className="text-3xl sm:text-4xl font-bold text-slate-50 tracking-tight leading-tight text-balance">
        {children}
      </h2>
      {sub && <p className="mt-3 text-base text-slate-400 max-w-lg mx-auto text-balance">{sub}</p>}
    </div>
  );
}

export function BigButton({ children, onClick, tone = "primary", disabled, full }) {
  const styles = {
    primary: "bg-cyan-400 hover:bg-cyan-300 text-slate-950",
    ghost: "bg-transparent border border-slate-700 hover:border-slate-500 text-slate-300",
    danger: "bg-red-500 hover:bg-red-400 text-white",
  };
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`rounded-2xl font-semibold text-lg px-8 py-4 transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${
        styles[tone]
      } ${full ? "w-full" : ""}`}
    >
      {children}
    </button>
  );
}

export function Rail({ steps, current }) {
  return (
    <div className="flex items-center justify-center gap-1.5" aria-hidden="true">
      {Array.from({ length: steps }, (_, i) => (
        <span
          key={i}
          className={`h-1 rounded-full transition-all duration-300 ${
            i < current ? "w-6 bg-cyan-500" : i === current ? "w-10 bg-cyan-400" : "w-6 bg-slate-800"
          }`}
        />
      ))}
    </div>
  );
}

export function Badge({ children, tone = "slate" }) {
  const styles = {
    slate: "bg-slate-800 text-slate-300",
    good: "bg-emerald-500/15 text-emerald-300",
    warn: "bg-amber-500/15 text-amber-300",
    bad: "bg-red-500/15 text-red-300",
  };
  return (
    <span className={`inline-block rounded-full px-3 py-1 text-xs font-semibold ${styles[tone]}`}>
      {children}
    </span>
  );
}
