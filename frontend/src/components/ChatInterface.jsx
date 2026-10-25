import React, { useEffect, useRef } from "react";
import { Volume2, Bot, User, Check, AlertCircle } from "lucide-react";
import { speechService } from "../services/speech";

export default function ChatInterface({ messages, language }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSpeak = (text) => {
    speechService.speak(text, language);
  };

  return (
    <div className="chat-container">
      {messages.map((msg, index) => {
        const isUser = msg.role === "user";
        return (
          <div
            key={index}
            className={`chat-bubble ${isUser ? "user" : "bot"}`}
          >
            {/* Header info for bot messages */}
            {!isUser && msg.intent && (
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 4 }}>
                <span className="intent-tag">
                  {msg.intent.replace(/_/g, " ")} {msg.confidence ? `(${(msg.confidence * 100).toFixed(0)}%)` : ""}
                </span>
                <button
                  onClick={() => handleSpeak(msg.text)}
                  style={{
                    background: "transparent",
                    border: "none",
                    color: "var(--text-muted)",
                    cursor: "pointer",
                    padding: 2,
                    display: "flex",
                    alignItems: "center"
                  }}
                  title="Listen to response"
                >
                  <Volume2 size={14} />
                </button>
              </div>
            )}

            <div style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
              <div style={{ marginTop: 2, color: isUser ? "#ffffff" : "var(--accent)" }}>
                {isUser ? <User size={15} /> : <Bot size={15} />}
              </div>
              <div style={{ flex: 1, whiteSpace: "pre-wrap" }}>
                {msg.text}
              </div>
            </div>

            <div style={{
              fontSize: "0.68rem",
              color: isUser ? "rgba(255, 255, 255, 0.7)" : "var(--text-dim)",
              textAlign: "right",
              marginTop: 4
            }}>
              {msg.time}
            </div>
          </div>
        );
      })}
      <div ref={bottomRef} />
    </div>
  );
}
