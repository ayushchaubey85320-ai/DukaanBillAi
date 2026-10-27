import React, { useState } from "react";
import { 
  X, LogIn, UserPlus, Shield, Store, Phone, Lock, User, 
  MapPin, CreditCard, FileText, CheckCircle2, AlertCircle, ArrowRight
} from "lucide-react";
import { loginUser, registerUser } from "../services/api";

export default function AuthModal({ isOpen, onClose, onAuthSuccess, initialTab = "login" }) {
  const [activeTab, setActiveTab] = useState(initialTab); // "login" | "register" | "admin"

  React.useEffect(() => {
    if (initialTab) setActiveTab(initialTab);
  }, [initialTab, isOpen]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  // Login Form State
  const [loginPhone, setLoginPhone] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  // Register Form State
  const [regData, setRegData] = useState({
    phone: "",
    password: "",
    full_name: "",
    shop_name: "",
    shop_type: "kirana",
    gstin: "",
    upi_id: "",
    address: ""
  });

  // Admin Form State
  const [adminPhone, setAdminPhone] = useState("");
  const [adminPassword, setAdminPassword] = useState("");

  if (!isOpen) return null;

  const handleShopkeeperLogin = async (e) => {
    e?.preventDefault();
    setErrorMessage("");
    setSuccessMessage("");
    setIsLoading(true);

    try {
      const res = await loginUser(loginPhone, loginPassword);
      setSuccessMessage(res.message || "Logged in successfully!");
      setTimeout(() => {
        onAuthSuccess(res.user);
        onClose();
      }, 700);
    } catch (err) {
      setErrorMessage(err.message || "Login failed. Check your mobile number and password.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e?.preventDefault();
    setErrorMessage("");
    setSuccessMessage("");
    setIsLoading(true);

    try {
      const res = await registerUser(regData);
      setSuccessMessage("Account created successfully! Logging you in...");
      setTimeout(() => {
        onAuthSuccess(res.user);
        onClose();
      }, 800);
    } catch (err) {
      setErrorMessage(err.message || "Registration failed. Please check your details.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleAdminLogin = async (e) => {
    e?.preventDefault();
    setErrorMessage("");
    setSuccessMessage("");
    setIsLoading(true);

    try {
      const res = await loginUser(adminPhone, adminPassword);
      if (res.user.role !== "super_admin") {
        throw new Error("This account does not have Super Admin privileges.");
      }
      setSuccessMessage("Super Admin access granted! Loading Master Portal...");
      setTimeout(() => {
        onAuthSuccess(res.user);
        onClose();
      }, 700);
    } catch (err) {
      setErrorMessage(err.message || "Invalid Super Admin credentials.");
    } finally {
      setIsLoading(false);
    }
  };

  // Demo Autofill helpers for quick preview without security exposure
  const fillDemoShopkeeper = () => {
    setLoginPhone("9876543210");
    setLoginPassword("Shop@1234");
    setErrorMessage("");
  };

  const fillDemoAdmin = () => {
    setAdminPhone("9999999999");
    setAdminPassword("SuperAdmin@2026");
    setErrorMessage("");
  };

  return (
    <div className="modal-backdrop" onClick={onClose} style={{ zIndex: 9999 }}>
      <div 
        className="modal-content glass-card"
        onClick={(e) => e.stopPropagation()}
        style={{
          maxWidth: activeTab === "register" ? 560 : 440,
          width: "92%",
          maxHeight: "90vh",
          overflowY: "auto",
          padding: 24,
          borderRadius: 20,
          background: "rgba(18, 24, 38, 0.96)",
          border: "1px solid rgba(255, 255, 255, 0.12)",
          boxShadow: "0 25px 60px rgba(0, 0, 0, 0.7)"
        }}
      >
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{
              width: 36,
              height: 36,
              borderRadius: 10,
              background: activeTab === "admin" 
                ? "linear-gradient(135deg, #f59e0b, #b45309)" 
                : "linear-gradient(135deg, #10b981, #047857)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#fff"
            }}>
              {activeTab === "admin" ? <Shield size={20} /> : <Store size={20} />}
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: "1.15rem", fontWeight: 700, color: "#fff" }}>
                {activeTab === "login" && "Shopkeeper Login"}
                {activeTab === "register" && "Create Dukaan Account"}
                {activeTab === "admin" && "Super Admin Portal"}
              </h3>
              <p style={{ margin: 0, fontSize: "0.78rem", color: "#94a3b8" }}>
                {activeTab === "login" && "Access your saved bills, counter & store profile"}
                {activeTab === "register" && "Register your store for live AI voice billing"}
                {activeTab === "admin" && "Owner-only portal to monitor stores and users"}
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            style={{
              background: "rgba(255,255,255,0.08)",
              border: "none",
              borderRadius: "50%",
              width: 32,
              height: 32,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#94a3b8",
              cursor: "pointer"
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Tab Switcher */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 6,
          background: "rgba(0, 0, 0, 0.35)",
          padding: 4,
          borderRadius: 12,
          marginBottom: 20
        }}>
          <button
            onClick={() => { setActiveTab("login"); setErrorMessage(""); }}
            style={{
              padding: "8px 6px",
              borderRadius: 8,
              border: "none",
              fontSize: "0.8rem",
              fontWeight: 600,
              cursor: "pointer",
              background: activeTab === "login" ? "rgba(16, 185, 129, 0.25)" : "transparent",
              color: activeTab === "login" ? "#34d399" : "#94a3b8",
              transition: "all 0.2s"
            }}
          >
            <LogIn size={13} style={{ display: "inline", marginRight: 4, verticalAlign: -2 }} />
            Login
          </button>
          <button
            onClick={() => { setActiveTab("register"); setErrorMessage(""); }}
            style={{
              padding: "8px 6px",
              borderRadius: 8,
              border: "none",
              fontSize: "0.8rem",
              fontWeight: 600,
              cursor: "pointer",
              background: activeTab === "register" ? "rgba(16, 185, 129, 0.25)" : "transparent",
              color: activeTab === "register" ? "#34d399" : "#94a3b8",
              transition: "all 0.2s"
            }}
          >
            <UserPlus size={13} style={{ display: "inline", marginRight: 4, verticalAlign: -2 }} />
            Register
          </button>
        </div>

        {/* Alert Messages */}
        {errorMessage && (
          <div style={{
            background: "rgba(239, 68, 68, 0.15)",
            border: "1px solid rgba(239, 68, 68, 0.35)",
            padding: "10px 14px",
            borderRadius: 10,
            fontSize: "0.82rem",
            color: "#fca5a5",
            marginBottom: 16,
            display: "flex",
            alignItems: "center",
            gap: 8
          }}>
            <AlertCircle size={16} />
            <span>{errorMessage}</span>
          </div>
        )}

        {successMessage && (
          <div style={{
            background: "rgba(16, 185, 129, 0.15)",
            border: "1px solid rgba(16, 185, 129, 0.35)",
            padding: "10px 14px",
            borderRadius: 10,
            fontSize: "0.82rem",
            color: "#6ee7b7",
            marginBottom: 16,
            display: "flex",
            alignItems: "center",
            gap: 8
          }}>
            <CheckCircle2 size={16} />
            <span>{successMessage}</span>
          </div>
        )}

        {/* 1. Shopkeeper Login Form */}
        {activeTab === "login" && (
          <form onSubmit={handleShopkeeperLogin} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", color: "#cbd5e1", marginBottom: 6 }}>
                Mobile Number (10 Digits)
              </label>
              <div style={{ position: "relative" }}>
                <Phone size={16} style={{ position: "absolute", left: 12, top: 12, color: "#94a3b8" }} />
                <input
                  type="tel"
                  required
                  placeholder="e.g. 9876543210"
                  value={loginPhone}
                  onChange={(e) => setLoginPhone(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "10px 12px 10px 38px",
                    background: "rgba(255, 255, 255, 0.05)",
                    border: "1px solid rgba(255, 255, 255, 0.15)",
                    borderRadius: 10,
                    color: "#fff",
                    fontSize: "0.9rem",
                    outline: "none"
                  }}
                />
              </div>
            </div>

            <div>
              <label style={{ display: "block", fontSize: "0.8rem", color: "#cbd5e1", marginBottom: 6 }}>
                Password
              </label>
              <div style={{ position: "relative" }}>
                <Lock size={16} style={{ position: "absolute", left: 12, top: 12, color: "#94a3b8" }} />
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "10px 12px 10px 38px",
                    background: "rgba(255, 255, 255, 0.05)",
                    border: "1px solid rgba(255, 255, 255, 0.15)",
                    borderRadius: 10,
                    color: "#fff",
                    fontSize: "0.9rem",
                    outline: "none"
                  }}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              style={{
                marginTop: 6,
                padding: "11px 16px",
                background: "linear-gradient(135deg, #10b981, #059669)",
                border: "none",
                borderRadius: 10,
                color: "#fff",
                fontWeight: 700,
                fontSize: "0.92rem",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 8,
                boxShadow: "0 4px 15px rgba(16, 185, 129, 0.4)"
              }}
            >
              {isLoading ? "Signing In..." : (
                <>
                  <span>Sign In to Dukaan</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>

            <div style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginTop: 4,
              paddingTop: 10,
              borderTop: "1px solid rgba(255, 255, 255, 0.08)",
              fontSize: "0.78rem"
            }}>
              <span style={{ color: "#94a3b8" }}>Need a demo account?</span>
              <button
                type="button"
                onClick={fillDemoShopkeeper}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#34d399",
                  fontWeight: 600,
                  cursor: "pointer",
                  textDecoration: "underline"
                }}
              >
                Autofill Demo Shop
              </button>
            </div>
          </form>
        )}

        {/* 2. Shopkeeper Registration Form */}
        {activeTab === "register" && (
          <form onSubmit={handleRegister} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <div>
                <label style={{ display: "block", fontSize: "0.78rem", color: "#cbd5e1", marginBottom: 4 }}>
                  Mobile Number *
                </label>
                <div style={{ position: "relative" }}>
                  <Phone size={14} style={{ position: "absolute", left: 10, top: 11, color: "#94a3b8" }} />
                  <input
                    type="tel"
                    required
                    placeholder="10 Digits"
                    value={regData.phone}
                    onChange={(e) => setRegData({ ...regData, phone: e.target.value })}
                    style={{
                      width: "100%",
                      padding: "8px 10px 8px 32px",
                      background: "rgba(255, 255, 255, 0.05)",
                      border: "1px solid rgba(255, 255, 255, 0.15)",
                      borderRadius: 8,
                      color: "#fff",
                      fontSize: "0.85rem",
                      outline: "none"
                    }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.78rem", color: "#cbd5e1", marginBottom: 4 }}>
                  Password *
                </label>
                <div style={{ position: "relative" }}>
                  <Lock size={14} style={{ position: "absolute", left: 10, top: 11, color: "#94a3b8" }} />
                  <input
                    type="password"
                    required
                    placeholder="Min 4 chars"
                    value={regData.password}
                    onChange={(e) => setRegData({ ...regData, password: e.target.value })}
                    style={{
                      width: "100%",
                      padding: "8px 10px 8px 32px",
                      background: "rgba(255, 255, 255, 0.05)",
                      border: "1px solid rgba(255, 255, 255, 0.15)",
                      borderRadius: 8,
                      color: "#fff",
                      fontSize: "0.85rem",
                      outline: "none"
                    }}
                  />
                </div>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <div>
                <label style={{ display: "block", fontSize: "0.78rem", color: "#cbd5e1", marginBottom: 4 }}>
                  Owner / Malik Name *
                </label>
                <div style={{ position: "relative" }}>
                  <User size={14} style={{ position: "absolute", left: 10, top: 11, color: "#94a3b8" }} />
                  <input
                    type="text"
                    required
                    placeholder="e.g. Ramesh Kumar"
                    value={regData.full_name}
                    onChange={(e) => setRegData({ ...regData, full_name: e.target.value })}
                    style={{
                      width: "100%",
                      padding: "8px 10px 8px 32px",
                      background: "rgba(255, 255, 255, 0.05)",
                      border: "1px solid rgba(255, 255, 255, 0.15)",
                      borderRadius: 8,
                      color: "#fff",
                      fontSize: "0.85rem",
                      outline: "none"
                    }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.78rem", color: "#cbd5e1", marginBottom: 4 }}>
                  Dukaan / Shop Name *
                </label>
                <div style={{ position: "relative" }}>
                  <Store size={14} style={{ position: "absolute", left: 10, top: 11, color: "#94a3b8" }} />
                  <input
                    type="text"
                    required
                    placeholder="e.g. Ramesh Kirana Store"
                    value={regData.shop_name}
                    onChange={(e) => setRegData({ ...regData, shop_name: e.target.value })}
                    style={{
                      width: "100%",
                      padding: "8px 10px 8px 32px",
                      background: "rgba(255, 255, 255, 0.05)",
                      border: "1px solid rgba(255, 255, 255, 0.15)",
                      borderRadius: 8,
                      color: "#fff",
                      fontSize: "0.85rem",
                      outline: "none"
                    }}
                  />
                </div>
              </div>
            </div>

            <div>
              <label style={{ display: "block", fontSize: "0.78rem", color: "#cbd5e1", marginBottom: 4 }}>
                Business Category
              </label>
              <select
                value={regData.shop_type}
                onChange={(e) => setRegData({ ...regData, shop_type: e.target.value })}
                style={{
                  width: "100%",
                  padding: "8px 10px",
                  background: "rgba(30, 41, 59, 0.9)",
                  border: "1px solid rgba(255, 255, 255, 0.15)",
                  borderRadius: 8,
                  color: "#fff",
                  fontSize: "0.85rem",
                  outline: "none"
                }}
              >
                <option value="kirana">Kirana & Grocery Store (किराना)</option>
                <option value="general">General Store / Supermarket</option>
                <option value="medical">Medical & Pharmacy (दवाखाना)</option>
                <option value="electronics">Electronics & Mobile Shop</option>
                <option value="garments">Garments & Clothing</option>
                <option value="hardware">Hardware & Sanitary Store</option>
                <option value="cafe">Cafe, Bakery & Snacks</option>
                <option value="other">Other Retail Business</option>
              </select>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <div>
                <label style={{ display: "block", fontSize: "0.78rem", color: "#cbd5e1", marginBottom: 4 }}>
                  GSTIN (Optional)
                </label>
                <div style={{ position: "relative" }}>
                  <FileText size={14} style={{ position: "absolute", left: 10, top: 11, color: "#94a3b8" }} />
                  <input
                    type="text"
                    placeholder="07AAAAA0000A1Z5"
                    value={regData.gstin}
                    onChange={(e) => setRegData({ ...regData, gstin: e.target.value })}
                    style={{
                      width: "100%",
                      padding: "8px 10px 8px 32px",
                      background: "rgba(255, 255, 255, 0.05)",
                      border: "1px solid rgba(255, 255, 255, 0.15)",
                      borderRadius: 8,
                      color: "#fff",
                      fontSize: "0.85rem",
                      outline: "none"
                    }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.78rem", color: "#cbd5e1", marginBottom: 4 }}>
                  UPI ID for QR (Optional)
                </label>
                <div style={{ position: "relative" }}>
                  <CreditCard size={14} style={{ position: "absolute", left: 10, top: 11, color: "#94a3b8" }} />
                  <input
                    type="text"
                    placeholder="shop@upi"
                    value={regData.upi_id}
                    onChange={(e) => setRegData({ ...regData, upi_id: e.target.value })}
                    style={{
                      width: "100%",
                      padding: "8px 10px 8px 32px",
                      background: "rgba(255, 255, 255, 0.05)",
                      border: "1px solid rgba(255, 255, 255, 0.15)",
                      borderRadius: 8,
                      color: "#fff",
                      fontSize: "0.85rem",
                      outline: "none"
                    }}
                  />
                </div>
              </div>
            </div>

            <div>
              <label style={{ display: "block", fontSize: "0.78rem", color: "#cbd5e1", marginBottom: 4 }}>
                Shop Address (Optional)
              </label>
              <div style={{ position: "relative" }}>
                <MapPin size={14} style={{ position: "absolute", left: 10, top: 11, color: "#94a3b8" }} />
                <input
                  type="text"
                  placeholder="e.g. Shop #4, Main Market, Delhi"
                  value={regData.address}
                  onChange={(e) => setRegData({ ...regData, address: e.target.value })}
                  style={{
                    width: "100%",
                    padding: "8px 10px 8px 32px",
                    background: "rgba(255, 255, 255, 0.05)",
                    border: "1px solid rgba(255, 255, 255, 0.15)",
                    borderRadius: 8,
                    color: "#fff",
                    fontSize: "0.85rem",
                    outline: "none"
                  }}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              style={{
                marginTop: 6,
                padding: "11px 16px",
                background: "linear-gradient(135deg, #10b981, #059669)",
                border: "none",
                borderRadius: 10,
                color: "#fff",
                fontWeight: 700,
                fontSize: "0.92rem",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 8,
                boxShadow: "0 4px 15px rgba(16, 185, 129, 0.4)"
              }}
            >
              {isLoading ? "Creating Account..." : (
                <>
                  <span>Create Account & Start Billing</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>
        )}

        {/* 3. Super Admin Login Form */}
        {activeTab === "admin" && (
          <form onSubmit={handleAdminLogin} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div style={{
              background: "rgba(245, 158, 11, 0.1)",
              border: "1px solid rgba(245, 158, 11, 0.25)",
              padding: "10px 14px",
              borderRadius: 10,
              fontSize: "0.78rem",
              color: "#fcd34d",
              display: "flex",
              alignItems: "flex-start",
              gap: 8
            }}>
              <Shield size={16} style={{ marginTop: 2, flexShrink: 0 }} />
              <div>
                <strong>Restricted Super Admin Portal:</strong> Reserved exclusively for the platform owner to track registered users, monitor bills created, and login/impersonate any store.
              </div>
            </div>

            <div>
              <label style={{ display: "block", fontSize: "0.8rem", color: "#cbd5e1", marginBottom: 6 }}>
                Master Admin Mobile
              </label>
              <div style={{ position: "relative" }}>
                <Phone size={16} style={{ position: "absolute", left: 12, top: 12, color: "#94a3b8" }} />
                <input
                  type="tel"
                  required
                  placeholder="Master Admin Phone"
                  value={adminPhone}
                  onChange={(e) => setAdminPhone(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "10px 12px 10px 38px",
                    background: "rgba(255, 255, 255, 0.05)",
                    border: "1px solid rgba(255, 255, 255, 0.15)",
                    borderRadius: 10,
                    color: "#fff",
                    fontSize: "0.9rem",
                    outline: "none"
                  }}
                />
              </div>
            </div>

            <div>
              <label style={{ display: "block", fontSize: "0.8rem", color: "#cbd5e1", marginBottom: 6 }}>
                Master Secret Password
              </label>
              <div style={{ position: "relative" }}>
                <Lock size={16} style={{ position: "absolute", left: 12, top: 12, color: "#94a3b8" }} />
                <input
                  type="password"
                  required
                  placeholder="••••••••••••"
                  value={adminPassword}
                  onChange={(e) => setAdminPassword(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "10px 12px 10px 38px",
                    background: "rgba(255, 255, 255, 0.05)",
                    border: "1px solid rgba(255, 255, 255, 0.15)",
                    borderRadius: 10,
                    color: "#fff",
                    fontSize: "0.9rem",
                    outline: "none"
                  }}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              style={{
                marginTop: 6,
                padding: "11px 16px",
                background: "linear-gradient(135deg, #f59e0b, #d97706)",
                border: "none",
                borderRadius: 10,
                color: "#1e1e1e",
                fontWeight: 800,
                fontSize: "0.92rem",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 8,
                boxShadow: "0 4px 15px rgba(245, 158, 11, 0.4)"
              }}
            >
              {isLoading ? "Authenticating Master..." : (
                <>
                  <Shield size={16} />
                  <span>Access Super Admin Portal</span>
                </>
              )}
            </button>

            <div style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginTop: 4,
              paddingTop: 10,
              borderTop: "1px solid rgba(255, 255, 255, 0.08)",
              fontSize: "0.78rem"
            }}>
              <span style={{ color: "#94a3b8" }}>Default Owner Credentials?</span>
              <button
                type="button"
                onClick={fillDemoAdmin}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#fbbf24",
                  fontWeight: 600,
                  cursor: "pointer",
                  textDecoration: "underline"
                }}
              >
                Autofill Owner Login
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
