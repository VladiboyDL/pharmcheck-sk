import { useEffect, useRef, useState } from "react";
import QRCode from "qrcode";
import { BigButton } from "./KioskShell";
import { API_ORIGIN, sendPlan } from "../../api/client";

/**
 * Getting the plan out of the kiosk and into the patient's hand.
 *
 * The QR used to carry the plan as plain text. A phone shows plain text and then
 * loses it — no file, no history, nothing to come back to. It now points at a page,
 * which the patient can bookmark, print, or turn into daily calendar reminders.
 * Reminders are the part that actually changes whether the medicine gets taken.
 */
export default function TakeAway({ data, onDone }) {
  const canvasRef = useRef(null);
  const [email, setEmail] = useState("");
  const [showEmail, setShowEmail] = useState(false);
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(null);

  const plan = data.dosing_plan ?? [];

  useEffect(() => {
    if (!canvasRef.current || !plan.length || !data.plan_token) return;
    const url = `${API_ORIGIN}/dispense/plan/${data.plan_token}`;
    QRCode.toCanvas(canvasRef.current, url, {
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
      // Only the token and the address travel; the body is built from what the
      // server already stored, so this cannot be used to mail arbitrary text.
      const res = await sendPlan({ token: data.plan_token, email });
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
        {data.compartment ? (
          <>
            <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-txt3">
              Lieky sú pripravené
            </p>
            <h2 className="mt-3 text-3xl font-semibold text-txt tracking-tighter2">
              Priehradka{" "}
              <span className="inline-block rounded-sm2 bg-brand px-3 py-1 font-mono text-ink">
                {data.compartment}
              </span>
            </h2>
            <p className="mt-4 text-base text-txt2 max-w-md mx-auto">
              Otvorí sa sama. Rozpis užívania si vezmite so sebou — naskenujte kód telefónom.
            </p>
          </>
        ) : (
          <>
            <h2 className="text-3xl font-semibold text-txt tracking-tighter2">
              Vezmite si rozpis so sebou
            </h2>
            <p className="mt-4 text-base text-txt2 max-w-md mx-auto">
              Naskenujte kód telefónom. Rozpis si uložíte a môžete si z neho nastaviť
              denné pripomienky.
            </p>
          </>
        )}

        <div className="mt-7 mx-auto rounded-card border border-hairline bg-surface p-4">
          <canvas ref={canvasRef} aria-label="QR kód s rozpisom liekov" />
        </div>

        <p className="mt-4 text-sm text-txt3">
          Na telefóne nájdete tlačidlo <span className="text-txt2">Pridať pripomienky do kalendára</span>.
        </p>

        {!showEmail && !sent && (
          <button
            onClick={() => setShowEmail(true)}
            className="mt-6 text-sm text-txt2 underline underline-offset-4 hover:text-txt"
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
              className="w-full rounded-card bg-panel border-2 border-hairline focus:border-brand focus:outline-none text-txt text-lg px-5 py-4 text-center"
            />
            <button
              type="submit"
              disabled={sending || !email}
              className="mt-3 w-full rounded-card bg-surface2 hover:bg-slate-700 disabled:opacity-40 text-txt text-lg py-4 transition"
            >
              {sending ? "Odosielam…" : "Odoslať"}
            </button>
          </form>
        )}

        {sent && (
          <div
            className={`mt-6 mx-auto max-w-sm rounded-card border px-4 py-3 text-sm ${
              sent.sent
                ? "border-ok/40 bg-ok/10 text-ok"
                : "border-hairline2 bg-surface text-txt2"
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
