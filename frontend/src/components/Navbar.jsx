import React from "react";
import { 
  Store, Languages, History, Settings, PlusCircle, 
  Smartphone, Shield, User, LogIn, LogOut 
} from "lucide-react";
import { getApiBase } from "../services/api";

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
  onLogout
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

      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", justifyContent: "flex-end" }}>
        {/* Super Admin Master Portal Button (Visible for Super Admin) */}
        {currentUser?.role === "super_admin" && (
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
        )}

        {/* User Account / Login Button */}
        {currentUser ? (
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            background: "rgba(255, 255, 255, 0.06)",
            border: "1px solid rgba(255, 255, 255, 0.12)",
            borderRadius: 8,
            padding: "4px 8px"
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 5, fontSize: "0.78rem", color: "#e2e8f0" }}>
              <User size={13} style={{ color: "#34d399" }} />
              <span style={{ fontWeight: 600, maxWidth: 100, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
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
            style={{ padding: "6px 12px", fontSize: "0.82rem", color: "#34d399", borderColor: "rgba(16, 185, 129, 0.3)" }}
            title="Login or Register Shopkeeper Account"
          >
            <LogIn size={15} />
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
          <Languages size={15} style={{ color: "var(--accent)" }} />
          <span>{language === "hi" ? "हिन्दी" : "English"}</span>
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
