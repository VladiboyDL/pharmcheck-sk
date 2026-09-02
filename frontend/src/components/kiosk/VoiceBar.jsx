/**
 * The voice agent's presence in the kiosk.
 *
 * Deliberately a thin strip, not a chat window: the patient is here to collect
 * medicine, and the agent narrates and answers rather than being the interface. It
 * hides itself entirely when voice is unavailable — dead controls are worse than
 * no controls.
 */
export default function VoiceBar({ status, speaking, muted, level, problem, onToggleMute, onRetry }) {
  if (status === "idle") return null;

  const connecting = status === "connecting";
  const failed = status === "error";

  return (
    <div className="flex items-center gap-3 px-6 sm:px-10 pt-4">
      <div
        className={`flex items-center gap-2.5 rounded-full border px-3 py-1.5 transition-colors ${
          failed
            ? "border-hairline bg-surface"
            : speaking
            ? "border-brand bg-brand/10"
            : "border-hairline bg-surface"
        }`}
      >
        <Meter level={muted ? 0 : level} active={speaking && !muted} connecting={connecting} />
        <span className={`text-[11px] ${speaking && !muted ? "text-brand" : "text-txt3"}`}>
          {failed
            ? problem ?? "Hlas nedostupný"
            : connecting
            ? "Pripájam…"
            : muted
            ? "Stlmené"
            : speaking
            ? "Hovorím"
            : "Počúvam"}
        </span>
      </div>

      <div className="flex-1" />

      {failed ? (
        <span className="flex items-center gap-3 text-[11px] text-txt3">
          <span>klikajte ďalej</span>
          <button onClick={onRetry} className="text-txt2 hover:text-txt underline underline-offset-2">
            alebo skúsiť znova
          </button>
        </span>
      ) : (
        <button
          onClick={onToggleMute}
          className="text-[11px] text-txt3 hover:text-txt2"
          aria-pressed={muted}
        >
          {muted ? "zapnúť zvuk" : "stlmiť"}
        </button>
      )}
    </div>
  );
}

/** Five bars driven by the agent's real output spectrum. */
function Meter({ level, active, connecting }) {
  const bars = [0.55, 0.85, 1, 0.8, 0.5];
  return (
    <span className="flex items-end gap-[3px] h-4" aria-hidden="true">
      {bars.map((weight, i) => {
        const height = connecting
          ? 35
          : active
          ? Math.max(18, Math.min(100, level * weight * 260))
          : 18;
        return (
          <span
            key={i}
            className={`w-[3px] rounded-full transition-[height] duration-75 ${
              active ? "bg-brand" : connecting ? "bg-slate-600 animate-pulse" : "bg-slate-700"
            }`}
            style={{ height: `${height}%` }}
          />
        );
      })}
    </span>
  );
}
