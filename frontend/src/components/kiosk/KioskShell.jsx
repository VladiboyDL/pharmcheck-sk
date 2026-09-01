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
      <h2 className="text-3xl sm:text-[2.6rem] font-semibold text-txt tracking-tighter2 leading-[1.05] text-balance">
        {children}
      </h2>
      {sub && <p className="mt-4 text-base text-txt2 max-w-lg mx-auto text-balance leading-relaxed">{sub}</p>}
    </div>
  );
}

export function BigButton({ children, onClick, tone = "primary", disabled, full }) {
  const styles = {
    // Black on the accent measures 5.4:1 where white is 3.9:1.
    primary: "bg-brand hover:bg-brandDeep hover:text-txt text-ink",
    ghost: "bg-transparent border border-hairline2 hover:border-white/30 text-txt2 hover:text-txt",
    danger: "bg-bad hover:brightness-110 text-ink",
  };
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`rounded-pill font-semibold text-lg px-8 py-4 transition-all duration-200 active:scale-[0.985] disabled:opacity-40 disabled:cursor-not-allowed ${
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
            i < current ? "w-6 bg-brand" : i === current ? "w-10 bg-brand" : "w-6 bg-surface2"
          }`}
        />
      ))}
    </div>
  );
}

export function Badge({ children, tone = "slate" }) {
  const styles = {
    slate: "bg-surface2 text-txt2",
    good: "bg-ok/15 text-ok",
    warn: "bg-warn/15 text-warn",
    bad: "bg-bad/15 text-bad",
  };
  return (
    <span className={`inline-block rounded-full px-3 py-1 text-xs font-semibold ${styles[tone]}`}>
      {children}
    </span>
  );
}
