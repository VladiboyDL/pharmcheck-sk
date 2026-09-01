import { useState, useRef, useEffect, useCallback } from "react";
import PharmacistAvatar from "./PharmacistAvatar";
import { pharmacistChat } from "../api/client";

const GREETING = {
  role: "assistant",
  content:
    "Dobrý deň, vitajte v lekárni. Som váš AI lekárnik. Povedzte mi, aké lieky užívate, a ja skontrolujem ich bezpečnosť.",
  drugs: [],
  interactions: [],
};

export default function PharmacistChat() {
  const [messages, setMessages] = useState([GREETING]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [avatarState, setAvatarState] = useState("idle");
  const [knownDrugs, setKnownDrugs] = useState([]);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [isListening, setIsListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const [audioData, setAudioData] = useState(null);
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);
  const recognitionRef = useRef(null);
  const synthRef = useRef(null);
  const audioCtxRef = useRef(null);
  const analyserRef = useRef(null);
  const animRef = useRef(null);

  // Check speech support
  useEffect(() => {
    const hasSpeech =
      "speechSynthesis" in window &&
      ("SpeechRecognition" in window || "webkitSpeechRecognition" in window);
    setSpeechSupported(hasSpeech);
    synthRef.current = window.speechSynthesis || null;
  }, []);

  // Auto-scroll
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Fake audio visualization when speaking (Web Speech API doesn't expose audio buffer)
  const startFakeAudioViz = useCallback(() => {
    const animate = () => {
      const data = new Uint8Array(64);
      for (let i = 0; i < 64; i++) {
        data[i] = Math.floor(80 + Math.random() * 150 * Math.sin(Date.now() / 200 + i * 0.3));
      }
      setAudioData(data);
      animRef.current = requestAnimationFrame(animate);
    };
    animate();
  }, []);

  const stopAudioViz = useCallback(() => {
    if (animRef.current) cancelAnimationFrame(animRef.current);
    setAudioData(null);
  }, []);

  // Speak text
  const speak = useCallback(
    (text) => {
      if (!voiceEnabled || !synthRef.current) return;
      synthRef.current.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = "sk-SK";
      utterance.rate = 0.92;
      utterance.pitch = 1.05;

      const voices = synthRef.current.getVoices();
      const skVoice = voices.find(
        (v) => v.lang.startsWith("sk") || v.lang.startsWith("cs")
      );
      if (skVoice) utterance.voice = skVoice;

      setAvatarState("talking");
      startFakeAudioViz();

      utterance.onend = () => {
        setAvatarState("idle");
        stopAudioViz();
      };
      utterance.onerror = () => {
        setAvatarState("idle");
        stopAudioViz();
      };
      synthRef.current.speak(utterance);
    },
    [voiceEnabled, startFakeAudioViz, stopAudioViz]
  );

  // Send message
  async function handleSend(text) {
    const trimmed = (text || input).trim();
    if (!trimmed || loading) return;

    // Stop any ongoing speech
    synthRef.current?.cancel();
    stopAudioViz();

    const userMsg = { role: "user", content: trimmed };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    setAvatarState("thinking");

    const historyForApi = messages
      .slice(-20)
      .map((m) => ({ role: m.role, content: m.content }));

    try {
      const res = await pharmacistChat(trimmed, historyForApi, knownDrugs);

      if (res.identified_drugs?.length > 0) {
        setKnownDrugs((prev) => {
          const ids = new Set(prev.map((d) => d.id));
          const newDrugs = res.identified_drugs.filter((d) => !ids.has(d.id));
          return [...prev, ...newDrugs];
        });
      }

      const assistantMsg = {
        role: "assistant",
        content: res.message,
        drugs: res.identified_drugs || [],
        interactions: res.interactions || [],
      };

      setMessages((prev) => [...prev, assistantMsg]);
      setAvatarState("idle");

      if (voiceEnabled) {
        speak(res.message);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Prepáčte, nastala chyba. Skúste to prosím znova.",
          drugs: [],
          interactions: [],
        },
      ]);
      setAvatarState("idle");
    } finally {
      setLoading(false);
    }
  }

  // Voice input
  function toggleListening() {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }

    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    const recognition = new SpeechRecognition();
    recognition.lang = "sk-SK";
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onstart = () => setIsListening(true);
    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((r) => r[0].transcript)
        .join("");
      setInput(transcript);
      if (event.results[0].isFinal) {
        setIsListening(false);
        handleSend(transcript);
      }
    };
    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => setIsListening(false);

    recognitionRef.current = recognition;
    recognition.start();
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleQuickAction(text) {
    setInput(text);
    handleSend(text);
  }

  return (
    <div
      className="relative -mx-4 -mt-6 rounded-none overflow-hidden"
      style={{
        minHeight: "calc(100vh - 130px)",
        background: "linear-gradient(180deg, #0f172a 0%, #1e1b4b 40%, #0f172a 100%)",
      }}
    >
      {/* Ambient background effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div
          className="absolute top-20 left-1/2 -translate-x-1/2 w-[500px] h-[500px] rounded-full opacity-10"
          style={{ background: "radial-gradient(circle, rgba(99,102,241,0.4), transparent 70%)" }}
        />
        <div
          className="absolute bottom-0 left-0 right-0 h-32 opacity-30"
          style={{ background: "linear-gradient(0deg, rgba(99,102,241,0.1), transparent)" }}
        />
      </div>

      <div className="relative z-10 max-w-2xl mx-auto flex flex-col px-4" style={{ height: "calc(100vh - 130px)" }}>
        {/* Avatar header */}
        <div className="flex flex-col items-center pt-6 pb-2 flex-shrink-0">
          <PharmacistAvatar state={avatarState} audioData={audioData} />

          <h2 className="mt-4 text-xl font-bold text-white tracking-wide">PharmBot</h2>
          <p className="text-xs text-indigo-300/70 font-medium tracking-widest uppercase">
            AI Lekárnik
          </p>

          {/* Known drugs pills */}
          {knownDrugs.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5 justify-center max-w-md">
              {knownDrugs.map((d) => (
                <span
                  key={d.id}
                  className="text-[10px] bg-indigo-500/20 text-indigo-200 px-2.5 py-0.5 rounded-full border border-indigo-400/20 font-medium backdrop-blur-sm"
                >
                  {d.trade_name}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Chat messages */}
        <div className="flex-1 overflow-y-auto px-1 space-y-3 pb-3 scrollbar-thin mt-2">
          {messages.map((msg, idx) => (
            <ChatBubble key={idx} message={msg} />
          ))}

          {/* Typing indicator */}
          {loading && (
            <div className="flex items-start gap-2.5">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500/30 to-violet-500/30 border border-indigo-400/20 flex items-center justify-center flex-shrink-0 backdrop-blur-sm">
                <svg className="w-4 h-4 text-indigo-300" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19 8l-4 4h3c0 3.31-2.69 6-6 6-1.01 0-1.97-.25-2.8-.7l-1.46 1.46C8.97 19.54 10.43 20 12 20c4.42 0 8-3.58 8-8h3l-4-4zM6 12c0-3.31 2.69-6 6-6 1.01 0 1.97.25 2.8.7l1.46-1.46C15.03 4.46 13.57 4 12 4c-4.42 0-8 3.58-8 8H1l4 4 4-4H6z" />
                </svg>
              </div>
              <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl rounded-tl-sm px-4 py-3">
                <div className="flex gap-1.5">
                  <div className="w-2 h-2 bg-indigo-400/60 rounded-full animate-bounce" style={{ animationDelay: "0s" }} />
                  <div className="w-2 h-2 bg-indigo-400/60 rounded-full animate-bounce" style={{ animationDelay: "0.15s" }} />
                  <div className="w-2 h-2 bg-indigo-400/60 rounded-full animate-bounce" style={{ animationDelay: "0.3s" }} />
                </div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Quick actions — only show at start */}
        {messages.length <= 1 && !loading && (
          <div className="flex-shrink-0 pb-3">
            <p className="text-center text-[11px] text-slate-400 mb-2.5">Skúste sa opýtať:</p>
            <div className="flex flex-wrap gap-2 justify-center">
              {[
                "Beriem warfarin a ibuprofen",
                "Užívam Zoloft a Tramal",
                "Mám predpísaný enalapril a draslík",
              ].map((q) => (
                <button
                  key={q}
                  onClick={() => handleQuickAction(q)}
                  className="text-xs bg-white/5 backdrop-blur-sm border border-white/10 text-slate-300 px-3.5 py-2 rounded-xl hover:bg-white/10 hover:border-indigo-400/30 hover:text-white transition-all"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input area */}
        <div className="flex-shrink-0 pb-4 pt-2">
          <div className="flex items-center gap-2 bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl px-3 py-2">
            {/* Voice toggle */}
            {speechSupported && (
              <button
                onClick={() => setVoiceEnabled(!voiceEnabled)}
                className={`p-2 rounded-xl transition-all flex-shrink-0 ${
                  voiceEnabled
                    ? "bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30"
                    : "text-slate-500 hover:text-slate-300 hover:bg-white/5"
                }`}
                title={voiceEnabled ? "Vypnúť hlas" : "Zapnúť hlas"}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {voiceEnabled ? (
                    <path
                      strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                      d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
                    />
                  ) : (
                    <path
                      strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                      d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2"
                    />
                  )}
                </svg>
              </button>
            )}

            {/* Text input */}
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isListening ? "Počúvam..." : "Napíšte lieky alebo otázku..."}
              disabled={loading || isListening}
              className={`flex-1 px-3 py-2 bg-transparent text-sm text-white placeholder-slate-500 focus:outline-none disabled:opacity-40 ${
                isListening ? "placeholder-red-400" : ""
              }`}
            />

            {/* Mic button */}
            {speechSupported && (
              <button
                onClick={toggleListening}
                disabled={loading}
                className={`p-2.5 rounded-xl transition-all flex-shrink-0 ${
                  isListening
                    ? "bg-red-500 text-white animate-pulse shadow-lg shadow-red-500/30"
                    : "text-slate-400 hover:text-white hover:bg-white/10"
                }`}
                title={isListening ? "Zastaviť" : "Hovoriť"}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                  />
                </svg>
              </button>
            )}

            {/* Send button */}
            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || loading}
              className="p-2.5 bg-indigo-500 hover:bg-indigo-400 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-xl transition-all shadow-lg shadow-indigo-500/20 hover:shadow-indigo-400/30 disabled:shadow-none flex-shrink-0"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* CSS animation for shimmer */}
      <style>{`
        @keyframes shimmer {
          0%, 100% { transform: translateX(-100%); }
          50% { transform: translateX(100%); }
        }
      `}</style>
    </div>
  );
}

/* ── Chat Bubble ── */
function ChatBubble({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex items-start gap-2.5 ${isUser ? "flex-row-reverse" : ""}`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500/30 to-violet-500/30 border border-indigo-400/20 flex items-center justify-center flex-shrink-0 backdrop-blur-sm">
          <svg className="w-4 h-4 text-indigo-300" viewBox="0 0 64 64" fill="currentColor">
            <circle cx="32" cy="20" r="10" opacity="0.8" />
            <path d="M16 52 L16 38 Q16 32 22 30 L28 28 Q32 27 36 28 L42 30 Q48 32 48 38 L48 52" opacity="0.7" />
            <rect x="30" y="38" width="4" height="10" rx="1" fill="rgba(255,255,255,0.3)" />
            <rect x="27" y="41" width="10" height="4" rx="1" fill="rgba(255,255,255,0.3)" />
          </svg>
        </div>
      )}

      <div className={`max-w-[80%] space-y-2 ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`px-4 py-3 text-sm leading-relaxed ${
            isUser
              ? "bg-indigo-500/80 backdrop-blur-sm text-white rounded-2xl rounded-tr-sm shadow-lg shadow-indigo-500/10"
              : "bg-white/8 backdrop-blur-md border border-white/10 text-slate-200 rounded-2xl rounded-tl-sm"
          }`}
        >
          {message.content}
        </div>

        {/* Interaction badges */}
        {message.interactions?.length > 0 && (
          <div className="space-y-1.5 pl-1">
            {message.interactions.map((inter, idx) => (
              <InteractionBadge key={idx} interaction={inter} />
            ))}
          </div>
        )}

        {/* Identified drugs */}
        {message.drugs?.length > 0 && (
          <div className="flex flex-wrap gap-1 pl-1">
            {message.drugs.map((d) => (
              <span
                key={d.id}
                className="text-[10px] bg-indigo-500/15 text-indigo-300 px-2 py-0.5 rounded-full border border-indigo-400/20"
              >
                {d.trade_name}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Interaction Badge ── */
function InteractionBadge({ interaction }) {
  const cfg = {
    "Závažná": { bg: "bg-red-500/15", border: "border-red-400/30", text: "text-red-300", badge: "bg-red-500" },
    "Stredná": { bg: "bg-amber-500/15", border: "border-amber-400/30", text: "text-amber-300", badge: "bg-amber-500" },
    "Mierna": { bg: "bg-emerald-500/15", border: "border-emerald-400/30", text: "text-emerald-300", badge: "bg-emerald-500" },
  };
  const c = cfg[interaction.severity] || cfg["Mierna"];

  return (
    <div className={`${c.bg} ${c.border} border rounded-xl px-3 py-2 text-xs backdrop-blur-sm`}>
      <div className="flex items-center gap-2">
        <span className={`${c.badge} text-white text-[9px] font-bold px-1.5 py-0.5 rounded-full`}>
          {interaction.severity}
        </span>
        <span className={`${c.text} font-medium`}>
          {interaction.drug_a} + {interaction.drug_b}
        </span>
      </div>
      {interaction.mechanism && (
        <p className={`${c.text} mt-1 opacity-70 leading-relaxed`}>{interaction.mechanism}</p>
      )}
    </div>
  );
}
