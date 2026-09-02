import { useCallback, useEffect, useRef, useState } from "react";
import { getVoiceConfig, openVoiceSession } from "../api/client";

/**
 * The kiosk's voice layer.
 *
 * Additive by design: every screen stays fully operable by tapping, so a failed
 * microphone, a noisy room or an unconfigured agent costs nothing. The patient's
 * medicines travel with the session as dynamic variables, so the agent talks about
 * their actual prescription rather than in generalities.
 */
export default function useVoiceAgent() {
  const [available, setAvailable] = useState(false);
  const [status, setStatus] = useState("idle"); // idle | connecting | live | error
  const [speaking, setSpeaking] = useState(false);
  const [muted, setMuted] = useState(false);
  const [level, setLevel] = useState(0);
  const [problem, setProblem] = useState(null); // why the voice dropped, in the patient's words
  const conversationRef = useRef(null);
  const frameRef = useRef(null);
  const watchdogRef = useRef(null);
  const speakingRef = useRef(false);

  const stop = useCallback(async () => {
    cancelAnimationFrame(frameRef.current);
    clearTimeout(watchdogRef.current);
    const conversation = conversationRef.current;
    conversationRef.current = null;
    setSpeaking(false);
    setLevel(0);
    setProblem(null);
    setStatus("idle");
    if (conversation) await conversation.endSession().catch(() => {});
  }, []);

  useEffect(() => {
    getVoiceConfig()
      .then((c) => setAvailable(Boolean(c.enabled)))
      .catch(() => setAvailable(false));
    return () => {
      cancelAnimationFrame(frameRef.current);
      conversationRef.current?.endSession?.().catch(() => {});
      conversationRef.current = null;
    };
  }, []);

  /** Real output levels from the agent's own stream — not a random walk. */
  const trackLevel = useCallback(() => {
    const tick = () => {
      const conversation = conversationRef.current;
      if (conversation) {
        try {
          const bytes = conversation.getOutputByteFrequencyData();
          const slice = bytes.slice(0, 24);
          const mean = slice.reduce((a, b) => a + b, 0) / (slice.length || 1);
          setLevel(mean / 255);
        } catch {
          setLevel(0);
        }
      }
      frameRef.current = requestAnimationFrame(tick);
    };
    tick();
  }, []);

  const start = useCallback(
    async ({ clientTools, firstMessage, ...context } = {}) => {
      if (conversationRef.current) return;
      setStatus("connecting");
      setProblem(null);
      try {
        const session = await openVoiceSession(context);
        if (!session.enabled || !session.signed_url) {
          setAvailable(false);
          setStatus("idle");
          return;
        }

        // Loaded on demand — the SDK carries a WebRTC stack and the kiosk must open
        // instantly whether or not anyone uses voice.
        const { Conversation } = await import("@elevenlabs/client");

        const conversation = await Conversation.startSession({
          signedUrl: session.signed_url,
          // get-signed-url mints a WebSocket URL; WebRTC needs a conversation token
          // from a different endpoint, so the transport has to match what we asked for.
          connectionType: "websocket",
          dynamicVariables: session.dynamic_variables,
          // The agent reads and drives the kiosk through these rather than through a
          // snapshot taken before the patient had even tapped their card.
          clientTools,
          // On a reconnect the agent must not greet and ask the question again.
          ...(firstMessage ? { overrides: { agent: { firstMessage } } } : {}),
          onModeChange: ({ mode }) => {
            speakingRef.current = mode === "speaking";
            setSpeaking(speakingRef.current);
          },
          onStatusChange: ({ status: s }) => {
            if (s === "connected") setStatus("live");
            else if (s !== "disconnected") setStatus(s);
            // "disconnected" is handled in onDisconnect, which knows why.
          },
          // The last live test died in silence: the patient spoke, nothing came back,
          // and a minute later the server closed the socket. If the model skips a
          // turn, a nudge after twelve quiet seconds makes it answer instead of
          // leaving the patient talking to a wall. Fires at most once per patient turn.
          onMessage: ({ source }) => {
            clearTimeout(watchdogRef.current);
            if (source !== "user") return;
            watchdogRef.current = setTimeout(() => {
              const c = conversationRef.current;
              if (!c || speakingRef.current) return;
              try {
                c.sendUserMessage("(Pacient čaká na odpoveď. Zisti stav obrazovky a pokračuj.)");
              } catch {
                /* voice is additive */
              }
            }, 12000);
          },
          onDisconnect: (details) => {
            cancelAnimationFrame(frameRef.current);
            clearTimeout(watchdogRef.current);
            conversationRef.current = null;
            setSpeaking(false);
            setLevel(0);
            // The agent hanging up after the goodbye is the happy path — the strip just
            // goes away. Anything else is a drop the patient has to be told about,
            // because otherwise they keep talking to a screen that no longer listens.
            const clean = details?.reason === "user" || (details?.reason === "agent" && (details.closeCode ?? 1000) === 1000);
            if (clean) {
              setStatus("idle");
            } else {
              setProblem("Hlas sa prerušil");
              setStatus("error");
            }
          },
          onError: () => {
            setProblem("Hlas sa prerušil");
            setStatus("error");
          },
        });

        conversationRef.current = conversation;
        setStatus("live");
        trackLevel();
      } catch {
        setStatus("error");
      }
    },
    [trackLevel]
  );

  /** Tell the agent where the patient now is, without waiting to be asked. */
  const say = useCallback((text) => {
    try {
      conversationRef.current?.sendContextualUpdate?.(text);
    } catch {
      /* voice is additive — never let it break the flow */
    }
  }, []);

  const toggleMute = useCallback(() => {
    setMuted((m) => {
      const next = !m;
      try {
        conversationRef.current?.setVolume?.({ volume: next ? 0 : 1 });
      } catch {
        /* ignore */
      }
      return next;
    });
  }, []);

  return { available, status, speaking, muted, level, problem, start, stop, say, toggleMute };
}
