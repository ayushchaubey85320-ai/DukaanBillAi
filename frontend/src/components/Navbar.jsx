import React, { useState, useEffect } from "react";
import { 
  Store, Languages, History, Settings, PlusCircle, 
  Smartphone, Shield, User, LogIn, LogOut, Database, Sparkles 
} from "lucide-react";
import { getApiBase, pingBackend } from "../services/api";

export default function Navbar({
  shopInfo,
  language,
  currentUser,
  onToggleLanguage,
  onOpenSettings,
  onOpenHistory,
  onResetBill,
  onOpenAuth,
  onOpenAdmin,
  onOpenServerModal,
  onLogout
}) {
  const [dbConnected, setDbConnected] = useState(true);

  useEffect(() => {
    pingBackend()
      .then(() => setDbConnected(true))
      .catch(() => setDbConnected(false));
  }, []);

  return (
    <header className="header-bar">
      {/* Brand & Store Profile */}
      <div className="brand-badge">
        <div style={{
          width: 42,
          height: 42,
          borderRadius: "var(--radius-md)",
          background: "linear-gradient(135deg, #10b981, #059669)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontWeight: 800,
          fontSize: "1.25rem",
          color: "#ffffff",
          boxShadow: "0 4px 14px rgba(16, 185, 129, 0.4)"
        }}>
          ₹
        </div>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span className="brand-title">DukaanAI</span>
            <span style={{
              fontSize: "0.68rem",
              background: "rgba(16, 185, 129, 0.18)",
              border: "1px solid rgba(16, 185, 129, 0.4)",
              color: "#34d399",
              padding: "1px 6px",
              borderRadius: "var(--radius-full)",
              fontWeight: 700,
              display: "flex",
              alignItems: "center",
              gap: 3
            }}>
              <Sparkles size={9} />
              Gemini 3.5
            </span>
          </div>
          <div className="brand-subtitle">
            {shopInfo?.name || "Retail Billing"} • <span style={{ color: "var(--accent)" }}>{shopInfo?.type?.toUpperCase() || "KIRANA"}</span>
          </div>
        </div>
      </div>

      {/* Nav Badges & Controls */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", justifyContent: "flex-end" }}>
        {/* MySQL Cloud Database Status Badge */}
        <button
          onClick={onOpenServerModal}
          className="btn-secondary"
          style={{
            padding: "5px 10px",
            fontSize: "0.78rem",
            background: dbConnected ? "rgba(16, 185, 129, 0.12)" : "rgba(239, 68, 68, 0.12)",
            borderColor: dbConnected ? "rgba(16, 185, 129, 0.35)" : "rgba(239, 68, 68, 0.35)",
            color: dbConnected ? "#6ee7b7" : "#fca5a5"
          }}
          title="Database: Aiven Cloud MySQL (Click to view server settings)"
        >
          <Database size={13} />
          <span>{dbConnected ? "MySQL Cloud" : "Offline Cache"}</span>
        </button>

        {/* Super Admin Access Button */}
        {currentUser?.role === "super_admin" ? (
          <button
            onClick={onOpenAdmin}
            style={{
              padding: "6px 12px",
              fontSize: "0.82rem",
              background: "linear-gradient(135deg, #f59e0b, #d97706)",
              color: "#1e1e1e",
              fontWeight: 800,
              border: "none",
              borderRadius: 8,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 6,
              boxShadow: "0 2px 10px rgba(245, 158, 11, 0.4)"
            }}
            title="Open Super Admin Master Portal"
          >
            <Shield size={15} />
            <span>Super Admin</span>
          </button>
        ) : (
          <button
            onClick={onOpenAdmin}
            className="btn-secondary"
            style={{
              padding: "5px 10px",
              fontSize: "0.78rem",
              background: "rgba(245, 158, 11, 0.12)",
              borderColor: "rgba(245, 158, 11, 0.35)",
              color: "#fbbf24"
            }}
            title="Super Admin Portal Login"
          >
            <Shield size={13} />
            <span>Admin</span>
          </button>
        )}

        {/* User Account / Login Button */}
        {currentUser ? (
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            background: "rgba(255, 255, 255, 0.06)",
            border: "1px solid rgba(255, 255, 255, 0.14)",
            borderRadius: 8,
            padding: "4px 8px"
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 5, fontSize: "0.78rem", color: "#e2e8f0" }}>
              <User size={13} style={{ color: "#34d399" }} />
              <span style={{ fontWeight: 600, maxWidth: 110, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {currentUser.shop_name || currentUser.full_name}
              </span>
            </div>
            <button
              onClick={onLogout}
              style={{
                background: "transparent",
                border: "none",
                color: "#94a3b8",
                cursor: "pointer",
                padding: "2px 4px",
                display: "flex",
                alignItems: "center"
              }}
              title="Logout"
            >
              <LogOut size={13} />
            </button>
          </div>
        ) : (
          <button
            onClick={onOpenAuth}
            className="btn-secondary"
            style={{ padding: "6px 12px", fontSize: "0.82rem", color: "#34d399", borderColor: "rgba(16, 185, 129, 0.35)" }}
            title="Login or Register Shopkeeper Account"
          >
            <LogIn size={14} />
            <span>Login / Register</span>
          </button>
        )}

        {/* Language Toggle */}
        <button
          onClick={onToggleLanguage}
          className="btn-secondary"
          style={{ padding: "6px 12px", fontSize: "0.82rem" }}
          title="Toggle Language (English / हिंदी)"
        >
          <Languages size={14} style={{ color: "var(--accent)" }} />
          <span>{language === "hi" ? "हिन्दी" : "English"}</span>
        </button>

        {/* Past Bills History */}
        <button
          onClick={onOpenHistory}
          className="btn-secondary"
          style={{ padding: "6px 12px", fontSize: "0.82rem" }}
          title="Past Bills History"
        >
          <History size={14} />
        </button>

        {/* Shop Profile Settings */}
        <button
          onClick={onOpenSettings}
          className="btn-secondary"
          style={{ padding: "6px 12px", fontSize: "0.82rem" }}
          title="Shop Profile Settings & GST"
        >
          <Settings size={14} />
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
          <Smartphone size={14} />
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
