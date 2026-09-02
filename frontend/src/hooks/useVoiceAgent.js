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
  const conversationRef = useRef(null);
  const frameRef = useRef(null);

  const stop = useCallback(async () => {
    cancelAnimationFrame(frameRef.current);
    const conversation = conversationRef.current;
    conversationRef.current = null;
    setSpeaking(false);
    setLevel(0);
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
    async ({ clientTools, ...context } = {}) => {
      if (conversationRef.current) return;
      setStatus("connecting");
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
          onModeChange: ({ mode }) => setSpeaking(mode === "speaking"),
          // When the agent ends the call itself (the patient said goodbye), the strip
          // disappears instead of reporting a disconnect nobody caused.
          onStatusChange: ({ status: s }) => {
            if (s === "connected") setStatus("live");
            else if (s === "disconnected") {
              cancelAnimationFrame(frameRef.current);
              conversationRef.current = null;
              setSpeaking(false);
              setLevel(0);
              setStatus("idle");
            } else setStatus(s);
          },
          onError: () => setStatus("error"),
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

  return { available, status, speaking, muted, level, start, stop, say, toggleMute };
}
