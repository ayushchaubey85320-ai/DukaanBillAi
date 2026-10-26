import React, { useState, useEffect } from "react";
import { Mic, MicOff, Send, Sparkles, Volume2, Square, X } from "lucide-react";
import { speechService } from "../services/speech";

const SUGGESTIONS = [
  "2 kg rice at 60 rs",
  "3 biscuit packet 20 each",
  "10% discount do",
  "GST 18% laga do",
  "Customer Ramesh 9876543210",
  "दो किलो चावल पैंसठ रुपये",
  "Bill dikhao",
  "Print invoice"
];

export default function VoiceController({ onSendMessage, isProcessing, language }) {
  const [inputText, setInputText] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [isAssistantSpeaking, setIsAssistantSpeaking] = useState(false);
  const [speechError, setSpeechError] = useState("");

  useEffect(() => {
    speechService.setSpeakingChangeListener((speaking) => {
      setIsAssistantSpeaking(speaking);
    });
    return () => {
      speechService.setSpeakingChangeListener(null);
    };
  }, []);

  const handleToggleVoice = () => {
    if (isListening) {
      // User manually taps to STOP recording
      const finalText = speechService.stopManualListening();
      setIsListening(false);
      const textToSend = (finalText || inputText).trim();
      if (textToSend) {
        onSendMessage(textToSend);
        setInputText("");
      }
    } else {
      // User manually taps to START recording
      setSpeechError("");
      speechService.setLanguage(language);
      speechService.startManualListening({
        initialText: inputText,
        onTranscriptUpdate: (fullTranscript) => {
          setInputText(fullTranscript);
        },
        onError: (err) => {
          setIsListening(false);
          setSpeechError(typeof err === "string" ? err : "Mic notice: Please speak clearly or type.");
        }
      });
      setIsListening(true);
    }
  };

  const handleCancelListening = () => {
    speechService.cancelManualListening();
    setIsListening(false);
    setInputText("");
  };

  const handleStopAssistantAudio = () => {
    speechService.cancelSpeech();
    setIsAssistantSpeaking(false);
  };

  const handleSend = (e) => {
    e?.preventDefault();
    if (isListening) {
      const finalText = speechService.stopManualListening();
      setIsListening(false);
      const toSend = (finalText || inputText).trim();
      if (toSend && !isProcessing) {
        onSendMessage(toSend);
        setInputText("");
      }
      return;
    }
    if (!inputText.trim() || isProcessing) return;
    onSendMessage(inputText.trim());
    setInputText("");
  };

  return (
    <div style={{ marginTop: "auto", padding: "10px 16px 14px", position: "relative" }}>
      {/* Assistant Speaking Audio Banner */}
      {isAssistantSpeaking && (
        <div style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: "linear-gradient(90deg, rgba(16, 185, 129, 0.25), rgba(59, 130, 246, 0.25))",
          border: "1px solid rgba(16, 185, 129, 0.4)",
          borderRadius: "var(--radius-md)",
          padding: "6px 12px",
          marginBottom: 8,
          fontSize: "0.82rem",
          color: "#6ee7b7",
          animation: "pulse 1.8s infinite"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <Volume2 size={16} className="text-emerald-400" />
            <span>Assistant is speaking audio response...</span>
          </div>
          <button
            onClick={handleStopAssistantAudio}
            style={{
              background: "rgba(239, 68, 68, 0.25)",
              border: "1px solid rgba(239, 68, 68, 0.5)",
              color: "#fca5a5",
              borderRadius: "var(--radius-sm)",
              padding: "2px 8px",
              fontSize: "0.74rem",
              fontWeight: 600,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 4
            }}
          >
            <Square size={10} fill="currentColor" />
            <span>Stop Audio</span>
          </button>
        </div>
      )}

      {/* Manual Recording Live Equalizer Bar */}
      {isListening && (
        <div style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: "linear-gradient(90deg, rgba(239, 68, 68, 0.2), rgba(249, 115, 22, 0.2))",
          border: "1px solid rgba(239, 68, 68, 0.5)",
          borderRadius: "var(--radius-md)",
          padding: "6px 12px",
          marginBottom: 8,
          fontSize: "0.82rem",
          color: "#fca5a5"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div className="audio-wave-bars">
              <span className="wave-bar"></span>
              <span className="wave-bar"></span>
              <span className="wave-bar"></span>
              <span className="wave-bar"></span>
            </div>
            <span style={{ fontWeight: 600, color: "#fff" }}>
              {language === "hi" ? "माइक चालू है (बोलते रहें)... पूरा होने पर लाल बटन दबाएं!" : "Mic is open (speak freely)... Tap mic again when finished!"}
            </span>
          </div>
          <button
            onClick={handleCancelListening}
            style={{
              background: "transparent",
              border: "none",
              color: "#fca5a5",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 2,
              fontSize: "0.75rem"
            }}
            title="Discard spoken audio"
          >
            <X size={14} />
            <span>Cancel</span>
          </button>
        </div>
      )}

      {/* Quick Suggestions Chips */}
      <div style={{
        display: "flex",
        gap: 8,
        overflowX: "auto",
        width: "100%",
        maxWidth: "100%",
        minWidth: 0,
        paddingBottom: 8,
        scrollbarWidth: "none"
      }}>
        {SUGGESTIONS.map((s, idx) => (
          <button
            key={idx}
            className="suggestion-pill"
            onClick={() => onSendMessage(s)}
            disabled={isProcessing || isListening}
          >
            <Sparkles size={11} style={{ display: "inline", marginRight: 4, color: "var(--accent)" }} />
            {s}
          </button>
        ))}
      </div>

      {speechError && (
        <div style={{
          fontSize: "0.78rem",
          color: "var(--warning)",
          marginBottom: 6,
          textAlign: "center"
        }}>
          {speechError}
        </div>
      )}

      {/* Input bar and Manual Floating Mic */}
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <form
          onSubmit={handleSend}
          style={{
            flex: 1,
            display: "flex",
            alignItems: "center",
            background: isListening ? "rgba(30, 41, 59, 0.9)" : "rgba(15, 23, 42, 0.8)",
            border: isListening ? "1.5px solid var(--accent)" : "1px solid var(--border-glass-strong)",
            borderRadius: "var(--radius-full)",
            padding: "4px 8px 4px 16px",
            boxShadow: isListening ? "0 0 16px rgba(16, 185, 129, 0.35)" : "var(--shadow-sm)",
            transition: "all 0.25s ease"
          }}
        >
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={
              isListening
                ? language === "hi" ? "सुन रहा हूँ... बोलिए (माइक खुला रहेगा)!" : "Listening... Speak continuously (mic stays open)!"
                : language === "hi" ? "बोलें या टाइप करें (उदा: 2 किलो चावल 60 rs)..." : "Speak or type items (e.g. 2 kg rice at 60 rs)..."
            }
            disabled={isProcessing}
            style={{
              flex: 1,
              background: "transparent",
              border: "none",
              outline: "none",
              color: "#ffffff",
              fontSize: "0.95rem"
            }}
          />
          {inputText && (
            <button
              type="button"
              onClick={() => setInputText("")}
              style={{
                background: "transparent",
                border: "none",
                color: "var(--text-dim)",
                cursor: "pointer",
                padding: "4px 6px",
                display: "flex",
                alignItems: "center"
              }}
              title="Clear text"
            >
              <X size={15} />
            </button>
          )}
          <button
            type="submit"
            disabled={(!inputText.trim() && !isListening) || isProcessing}
            style={{
              background: (inputText.trim() || isListening) ? "var(--accent)" : "rgba(255, 255, 255, 0.1)",
              border: "none",
              width: 38,
              height: 38,
              borderRadius: "var(--radius-full)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#ffffff",
              cursor: (inputText.trim() || isListening) ? "pointer" : "default",
              transition: "all 0.2s ease",
              boxShadow: (inputText.trim() || isListening) ? "0 2px 8px rgba(16, 185, 129, 0.4)" : "none"
            }}
            title={isListening ? "Complete & Send" : "Send message"}
          >
            <Send size={16} />
          </button>
        </form>

        {/* Manual Mic Button */}
        <div className="mic-fab-container">
          <button
            type="button"
            className={`mic-fab ${isListening ? "listening active-recording" : ""}`}
            onClick={handleToggleVoice}
            disabled={isProcessing}
            title={
              isListening
                ? "Tap to STOP and process your speech"
                : "Tap to START speaking (mic stays open until you tap again)"
            }
          >
            {isListening ? <MicOff size={26} /> : <Mic size={26} />}
          </button>
        </div>
      </div>
    </div>
  );
}
