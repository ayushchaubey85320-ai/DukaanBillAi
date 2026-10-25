import React, { useState } from "react";
import { Mic, MicOff, Send, Sparkles } from "lucide-react";
import { speechService } from "../services/speech";

const SUGGESTIONS = [
  "2 kg rice at 60 rs",
  "3 biscuit packet 20 each",
  "10% discount do",
  "GST 18% laga do",
  "Bill dikhao",
  "Customer Ramesh 9876543210",
  "Print invoice",
  "दो किलो चावल पैंसठ रुपये"
];

export default function VoiceController({ onSendMessage, isProcessing, language }) {
  const [inputText, setInputText] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [speechError, setSpeechError] = useState("");

  const handleToggleVoice = () => {
    if (isListening) {
      speechService.stopListening();
      setIsListening(false);
    } else {
      setSpeechError("");
      speechService.setLanguage(language);
      speechService.startListening(
        (finalTranscript) => {
          setIsListening(false);
          setInputText("");
          if (finalTranscript) {
            onSendMessage(finalTranscript);
          }
        },
        (interimTranscript) => {
          // Live real-time speech-to-text feedback!
          setInputText(interimTranscript);
        },
        (error) => {
          setIsListening(false);
          setSpeechError(typeof error === "string" ? error : "Voice error. Try typing.");
        },
        () => {
          setIsListening(false);
        }
      );
      setIsListening(true);
    }
  };

  const handleSend = (e) => {
    e.preventDefault();
    if (!inputText.trim() || isProcessing) return;
    onSendMessage(inputText.trim());
    setInputText("");
  };

  return (
    <div style={{ marginTop: "auto", padding: "12px 16px 16px" }}>
      {/* Suggestions Row */}
      <div style={{
        display: "flex",
        gap: 8,
        overflowX: "auto",
        width: "100%",
        maxWidth: "100%",
        minWidth: 0,
        paddingBottom: 10,
        scrollbarWidth: "none"
      }}>
        {SUGGESTIONS.map((s, idx) => (
          <button
            key={idx}
            className="suggestion-pill"
            onClick={() => onSendMessage(s)}
            disabled={isProcessing}
          >
            <Sparkles size={12} style={{ display: "inline", marginRight: 4, color: "var(--accent)" }} />
            {s}
          </button>
        ))}
      </div>

      {speechError && (
        <div style={{
          fontSize: "0.78rem",
          color: "var(--warning)",
          marginBottom: 8,
          textAlign: "center"
        }}>
          {speechError}
        </div>
      )}

      {/* Input bar and Floating Mic */}
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <form
          onSubmit={handleSend}
          style={{
            flex: 1,
            display: "flex",
            alignItems: "center",
            background: "rgba(15, 23, 42, 0.8)",
            border: "1px solid var(--border-glass-strong)",
            borderRadius: "var(--radius-full)",
            padding: "4px 8px 4px 18px",
            boxShadow: "var(--shadow-sm)"
          }}
        >
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={
              isListening
                ? language === "hi" ? "सुन रहा हूँ... बोलिए!" : "Listening... Speak now!"
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
          <button
            type="submit"
            disabled={!inputText.trim() || isProcessing}
            style={{
              background: inputText.trim() ? "var(--accent)" : "rgba(255, 255, 255, 0.1)",
              border: "none",
              width: 38,
              height: 38,
              borderRadius: "var(--radius-full)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#ffffff",
              cursor: inputText.trim() ? "pointer" : "default",
              transition: "all 0.2s ease"
            }}
          >
            <Send size={16} />
          </button>
        </form>

        {/* Pulsing Floating Action Mic */}
        <div className="mic-fab-container">
          <button
            type="button"
            className={`mic-fab ${isListening ? "listening" : ""}`}
            onClick={handleToggleVoice}
            disabled={isProcessing}
            title={isListening ? "Stop listening" : "Tap and speak item or bill command"}
          >
            {isListening ? <MicOff size={28} /> : <Mic size={28} />}
          </button>
        </div>
      </div>
    </div>
  );
}
