import { useEffect, useRef, useState } from "react";
import { getDemoCards, readCard, verifyBiometric } from "../../api/client";
import { Screen, Title, BigButton } from "./KioskShell";

/**
 * Card, then face. One instruction on screen at a time.
 *
 * The Slovak preukaz poistenca has no chip and no NFC — it is printed plastic. So the
 * card step is optical: the card goes under the camera and OCR lifts the name, birth
 * number and insurer code off the front. Starting the camera here also gets the
 * permission prompt out of the way before it can interrupt the face step.
 */
export default function KioskIdentity({ onDone, controls }) {
  const [cards, setCards] = useState([]);
  const [stage, setStage] = useState("card"); // card | reading | face | scanning
  const [patient, setPatient] = useState(null);
  const [cardMeta, setCardMeta] = useState(null);
  const [score, setScore] = useState(0);
  const [cameraOk, setCameraOk] = useState(false);
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    getDemoCards().then((d) => setCards(d.cards)).catch(() => {});
    startCamera();
    return () => streamRef.current?.getTracks().forEach((t) => t.stop());
  }, []);

  async function startCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user" },
        audio: false,
      });
      streamRef.current = stream;
      attach();
      setCameraOk(true);
    } catch {
      setCameraOk(false);
    }
  }

  function attach() {
    if (videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current;
      videoRef.current.play().catch(() => {});
    }
  }
  useEffect(attach, [stage, cameraOk]);

  async function scanCard(cardId) {
    setStage("reading");
    await new Promise((r) => setTimeout(r, 1100)); // OCR pass
    const data = await readCard(cardId);
    setPatient(data.patient);
    setCardMeta(data);
    setStage("face");
  }

  async function scanFace() {
    setStage("scanning");
    const result = await verifyBiometric(patient.card_id, { frameSignature: `k${Date.now()}` });
    const target = result.match_score ?? 0;
    for (let i = 1; i <= 24; i++) {
      await new Promise((r) => setTimeout(r, 50));
      setScore(Number(((target * i) / 24).toFixed(1)));
    }
    streamRef.current?.getTracks().forEach((t) => t.stop());
    onDone({ patient, biometric: result });
  }

  const card = cards[0];

  // The voice agent advances the same actions the buttons do — one code path, so the
  // two modes can never drift apart.
  useEffect(() => {
    if (!controls) return;
    controls.current = {
      stage,
      next: () => {
        if (stage === "card" && card) scanCard(card.card_id);
        else if (stage === "face") scanFace();
      },
    };
  }, [controls, stage, card]);

  // ── Card under the camera ──────────────────────────────────────────────────
  if (stage === "card" || stage === "reading") {
    return (
      <Screen
        footer={
          <BigButton
            onClick={() => card && scanCard(card.card_id)}
            disabled={!card || stage === "reading"}
            tone="ghost"
            full
          >
            {stage === "reading" ? "Čítam kartu…" : "Simulovať priloženie karty"}
          </BigButton>
        }
      >
        <div className="flex flex-col items-center">
          <Viewfinder
            videoRef={videoRef}
            cameraOk={cameraOk}
            aspect="aspect-[16/10]"
            scanning={stage === "reading"}
          >
            <div
              className={`absolute inset-x-[12%] top-1/2 -translate-y-1/2 aspect-[1.586] rounded-xl border-2 transition-colors ${
                stage === "reading" ? "border-cyan-400" : "border-slate-500/70 border-dashed"
              }`}
            />
          </Viewfinder>

          <div className="mt-6">
            <Title
              sub={
                stage === "reading"
                  ? "Načítavam meno, rodné číslo a kód poisťovne"
                  : "Položte ju pod kameru prednou stranou nahor"
              }
            >
              {stage === "reading" ? "Čítam kartu…" : "Priložte kartu poistenca"}
            </Title>
          </div>
        </div>
      </Screen>
    );
  }

  // ── Face against the card record ───────────────────────────────────────────
  return (
    <Screen
      footer={
        <BigButton onClick={scanFace} disabled={stage === "scanning"} full>
          {stage === "scanning" ? `Overujem… ${score.toFixed(0)} %` : "Overiť totožnosť"}
        </BigButton>
      }
    >
      <div className="flex flex-col items-center">
        <Viewfinder
          videoRef={videoRef}
          cameraOk={cameraOk}
          aspect="aspect-[3/4] max-w-[15rem]"
          scanning={stage === "scanning"}
        >
          <div
            className={`absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-36 h-48 rounded-[45%] border-2 transition-colors ${
              stage === "scanning" ? "border-cyan-400" : "border-slate-500/60"
            }`}
          />
        </Viewfinder>

        <div className="mt-6">
          <Title sub={`Karta patrí ${patient.name}. Pozrite sa prosím do kamery.`}>
            Overenie totožnosti
          </Title>
          {cardMeta && (
            <p className="mt-3 text-center text-[11px] text-slate-600">
              {cardMeta.channel} · {cardMeta.patient.birth_id_masked} · {cardMeta.patient.insurer}
            </p>
          )}
        </div>
      </div>
      <style>{`@keyframes kioskSweep{0%{top:12%}50%{top:84%}100%{top:12%}}`}</style>
    </Screen>
  );
}

function Viewfinder({ videoRef, cameraOk, aspect, scanning, children }) {
  return (
    <div className={`relative w-full ${aspect} rounded-2xl overflow-hidden bg-slate-900 border border-slate-800`}>
      <video
        ref={videoRef}
        muted
        playsInline
        className={`w-full h-full object-cover ${cameraOk ? "" : "opacity-0"}`}
        style={{ transform: "scaleX(-1)" }}
      />
      {!cameraOk && (
        <div className="absolute inset-0 grid place-items-center px-6 text-center">
          <p className="text-[11px] text-slate-500">
            Kamera nie je dostupná — beží simulovaný režim
          </p>
        </div>
      )}
      <div className="absolute inset-0 pointer-events-none">
        {children}
        {scanning && (
          <div className="absolute left-0 right-0 h-0.5 bg-cyan-400/80 shadow-[0_0_14px_3px_rgba(34,211,238,0.55)] animate-[kioskSweep_1.4s_ease-in-out_infinite]" />
        )}
      </div>
    </div>
  );
}
