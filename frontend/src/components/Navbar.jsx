import React from "react";
import { Store, Languages, History, CheckCircle2, Settings, PlusCircle, Smartphone, Globe } from "lucide-react";
import { getApiBase } from "../services/api";

export default function Navbar({
  shopInfo,
  language,
  onToggleLanguage,
  onOpenSettings,
  onOpenServerSettings,
  onOpenHistory,
  onOpenTests,
  onResetBill
}) {
  return (
    <header className="header-bar">
      <div className="brand-badge">
        <div style={{
          width: 38,
          height: 38,
          borderRadius: 10,
          background: "linear-gradient(135deg, var(--accent), #b45309)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontWeight: 800,
          fontSize: "1.2rem",
          color: "#fff",
          boxShadow: "0 2px 10px rgba(217, 119, 6, 0.4)"
        }}>
          ₹
        </div>
        <div>
          <div className="brand-title">DukaanAI</div>
          <div className="brand-subtitle">
            {shopInfo?.name || "Retail Billing"} • <span style={{ color: "var(--accent)" }}>{shopInfo?.type?.toUpperCase() || "KIRANA"}</span>
          </div>
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        {/* Language Toggle */}
        <button
          onClick={onToggleLanguage}
          className="btn-secondary"
          style={{ padding: "6px 12px", fontSize: "0.82rem" }}
          title="Toggle Language (English / हिंदी)"
        >
          <Languages size={15} style={{ color: "var(--accent)" }} />
          <span>{language === "hi" ? "हिन्दी" : "English"}</span>
        </button>

        {/* Server Connection Setting */}
        <button
          onClick={onOpenServerSettings}
          className="btn-secondary"
          style={{ padding: "6px 12px", fontSize: "0.82rem", color: "#10b981" }}
          title="Server Connection Settings (Online / Wi-Fi)"
        >
          <Globe size={15} />
          <span style={{ display: "none", sm: "inline" }}>Server</span>
        </button>

        {/* 21-Scenario Test Matrix Button */}
        <button
          onClick={onOpenTests}
          className="btn-secondary"
          style={{ padding: "6px 12px", fontSize: "0.82rem" }}
          title="Open Automated 21-Scenario Test Matrix"
        >
          <CheckCircle2 size={15} style={{ color: "var(--success)" }} />
          <span style={{ display: "none", sm: "inline" }}>21 Tests</span>
        </button>

        {/* Past Bills History */}
        <button
          onClick={onOpenHistory}
          className="btn-secondary"
          style={{ padding: "6px 12px", fontSize: "0.82rem" }}
          title="Past Bills History"
        >
          <History size={15} />
        </button>

        {/* Shop Profile Settings */}
        <button
          onClick={onOpenSettings}
          className="btn-secondary"
          style={{ padding: "6px 12px", fontSize: "0.82rem" }}
          title="Shop Profile Settings & GST"
        >
          <Settings size={15} />
        </button>

        {/* Download Android APK Button */}
        <a
          href={`${getApiBase()}/download-apk`}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-secondary"
          style={{ padding: "6px 12px", fontSize: "0.82rem", textDecoration: "none", color: "var(--success)" }}
          title="Download Android APK"
        >
          <Smartphone size={15} />
          <span>APK</span>
        </a>

        {/* New Bill Button */}
        <button
          onClick={onResetBill}
          className="btn-primary"
          style={{ padding: "6px 14px", fontSize: "0.82rem" }}
          title="Start New Bill"
        >
          <PlusCircle size={15} />
          <span>New Bill</span>
        </button>
      </div>
    </header>
  );
}
