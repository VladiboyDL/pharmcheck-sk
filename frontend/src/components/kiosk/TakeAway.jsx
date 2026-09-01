import { useEffect, useRef, useState } from "react";
import QRCode from "qrcode";
import { BigButton } from "./KioskShell";
import { sendPlan } from "../../api/client";

/**
 * Getting the plan out of the kiosk and into the patient's hand.
 *
 * The QR carries the plan as plain text, so the phone shows it with no network, no
 * app and no account — which also means nothing about the patient's medication
 * leaves the room. Email is offered because people ask for it, but it is genuinely
 * the worse channel: health data over ordinary mail is a GDPR problem, not a feature.
 */
export default function TakeAway({ data, onDone }) {
  const canvasRef = useRef(null);
  const [email, setEmail] = useState("");
  const [showEmail, setShowEmail] = useState(false);
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(null);

  const plan = data.dosing_plan ?? [];

  useEffect(() => {
    if (!canvasRef.current || !plan.length) return;
    // A QR tops out around 1.8 kB. Slovak diacritics cost two bytes each, so a long
    // regimen is trimmed to the schedule rather than being silently unencodable.
    let text = planText(data, true);
    if (byteLength(text) > 1500) text = planText(data, false);
    QRCode.toCanvas(canvasRef.current, text, {
      width: 208,
      margin: 1,
      errorCorrectionLevel: "L",
      color: { dark: "#e2e8f0", light: "#00000000" },
    }).catch(() => {});
  }, [data]);

  async function submit(e) {
    e.preventDefault();
    setSending(true);
    try {
      const res = await sendPlan({
        auditId: data.audit.audit_id,
        email,
        patientName: data.patient?.name,
        plan,
        advisories: (data.next_steps ?? [])
          .flatMap((s) => s.script ?? [])
          .map((l) => l.patient)
          .filter(Boolean),
      });
      setSent(res);
    } catch {
      setSent({ sent: false, reason: "Odoslanie zlyhalo." });
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="min-h-[34rem] flex flex-col">
      <div className="flex-1 flex flex-col justify-center text-center">
        <h2 className="text-3xl font-bold text-slate-50 tracking-tight">Vezmite si rozpis so sebou</h2>
        <p className="mt-3 text-base text-slate-400 max-w-md mx-auto">
          Naskenujte kód telefónom. Otvorí sa aj bez internetu a nikde sa neukladá.
        </p>

        <div className="mt-7 mx-auto rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
          <canvas ref={canvasRef} aria-label="QR kód s rozpisom liekov" />
        </div>

        {!showEmail && !sent && (
          <button
            onClick={() => setShowEmail(true)}
            className="mt-6 text-sm text-slate-400 underline underline-offset-4 hover:text-slate-200"
          >
            Radšej poslať e-mailom
          </button>
        )}

        {showEmail && !sent && (
          <form onSubmit={submit} className="mt-6 mx-auto w-full max-w-sm">
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="vas@email.sk"
              className="w-full rounded-2xl bg-slate-900 border-2 border-slate-800 focus:border-cyan-600 focus:outline-none text-slate-100 text-lg px-5 py-4 text-center"
            />
            <button
              type="submit"
              disabled={sending || !email}
              className="mt-3 w-full rounded-2xl bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-100 text-lg py-4 transition"
            >
              {sending ? "Odosielam…" : "Odoslať"}
            </button>
          </form>
        )}

        {sent && (
          <div
            className={`mt-6 mx-auto max-w-sm rounded-2xl border px-4 py-3 text-sm ${
              sent.sent
                ? "border-emerald-800 bg-emerald-950/40 text-emerald-200"
                : "border-slate-700 bg-slate-900/60 text-slate-400"
            }`}
          >
            {sent.sent ? `Rozpis sme odoslali na ${email}.` : sent.reason}
          </div>
        )}
      </div>

      <div className="pt-6">
        <BigButton onClick={onDone} full>
          Hotovo, ďakujem
        </BigButton>
      </div>
    </div>
  );
}

/** Same text the email would carry, small enough for a QR. */
function planText(data, withAdvice) {
  const lines = [`Rozpis liekov — ${data.patient?.name ?? ""}`, ""];
  for (const e of data.dosing_plan ?? []) {
    lines.push(e.trade_name);
    lines.push(`  ${e.schedule}`);
    if (withAdvice && e.when) lines.push(`  ${e.when}`);
    if (withAdvice && e.avoid) lines.push(`  Pozor: ${e.avoid}`);
    lines.push("");
  }
  lines.push("AvatarAI Dispense — nenahrádza pokyny lekára.");
  return lines.join("\n");
}

function byteLength(text) {
  return new TextEncoder().encode(text).length;
}
