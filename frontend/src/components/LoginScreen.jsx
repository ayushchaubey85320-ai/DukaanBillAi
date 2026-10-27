import React, { useState } from "react";
import { 
  LogIn, UserPlus, Store, Phone, Lock, User, MapPin, 
  CreditCard, FileText, CheckCircle2, AlertCircle, ArrowRight, 
  Sparkles, Download, Database, ShieldCheck
} from "lucide-react";
import { loginUser, registerUser, getApiBase } from "../services/api";

export default function LoginScreen({ onAuthSuccess }) {
  const [activeTab, setActiveTab] = useState("login"); // "login" | "register"
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  // Login Form
  const [loginPhone, setLoginPhone] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  // Register Form
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

  const handleLogin = async (e) => {
    e?.preventDefault();
    setErrorMessage("");
    setSuccessMessage("");
    setIsLoading(true);

    try {
      const res = await loginUser(loginPhone, loginPassword);
      setSuccessMessage(res.message || "स्वागत है! लॉग इन सफल हुआ...");
      setTimeout(() => {
        onAuthSuccess(res.user);
      }, 600);
    } catch (err) {
      setErrorMessage(err.message || "लॉग इन विफल रहा। कृपया मोबाइल नंबर और पासवर्ड जांचें।");
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
      setSuccessMessage("दुकान खाता सफलतापूर्वक बन गया! लॉग इन हो रहा है...");
      setTimeout(() => {
        onAuthSuccess(res.user);
      }, 700);
    } catch (err) {
      setErrorMessage(err.message || "पंजीकरण विफल रहा। कृपया सही जानकारी भरें।");
    } finally {
      setIsLoading(false);
    }
  };

  const apkUrl = `${getApiBase()}/download-apk`;

  return (
    <div style={{
      minHeight: "100vh",
      width: "100vw",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "radial-gradient(circle at 50% 20%, #1e293b 0%, #0f172a 65%, #020617 100%)",
      padding: "24px 16px",
      fontFamily: "'Inter', sans-serif",
      position: "relative",
      overflowX: "hidden"
    }}>
      {/* Decorative ambient glowing orbs */}
      <div style={{
        position: "absolute",
        top: "-10%",
        left: "20%",
        width: 400,
        height: 400,
        borderRadius: "50%",
        background: "radial-gradient(circle, rgba(16, 185, 129, 0.15) 0%, transparent 70%)",
        pointerEvents: "none",
        filter: "blur(40px)"
      }} />
      <div style={{
        position: "absolute",
        bottom: "-10%",
        right: "20%",
        width: 400,
        height: 400,
        borderRadius: "50%",
        background: "radial-gradient(circle, rgba(56, 189, 248, 0.12) 0%, transparent 70%)",
        pointerEvents: "none",
        filter: "blur(40px)"
      }} />

      <div style={{
        width: "100%",
        maxWidth: 500,
        background: "rgba(15, 23, 42, 0.85)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        border: "1px solid rgba(255, 255, 255, 0.12)",
        borderRadius: 24,
        boxShadow: "0 25px 60px -15px rgba(0, 0, 0, 0.7), 0 0 30px rgba(16, 185, 129, 0.15)",
        overflow: "hidden",
        position: "relative",
        zIndex: 10
      }}>
        {/* Header Branding */}
        <div style={{
          padding: "32px 28px 24px",
          textAlign: "center",
          borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
          background: "linear-gradient(180deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.3) 100%)"
        }}>
          <div style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            width: 64,
            height: 64,
            borderRadius: 20,
            background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
            color: "#ffffff",
            fontSize: "2rem",
            fontWeight: 800,
            boxShadow: "0 8px 25px rgba(16, 185, 129, 0.4)",
            marginBottom: 16
          }}>
            ₹
          </div>

          <h1 style={{
            fontSize: "1.85rem",
            fontWeight: 800,
            color: "#ffffff",
            margin: "0 0 6px 0",
            letterSpacing: "-0.02em",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 10
          }}>
            <span>DukaanAI</span>
            <span style={{
              fontSize: "0.72rem",
              background: "rgba(16, 185, 129, 0.18)",
              border: "1px solid rgba(16, 185, 129, 0.4)",
              color: "#34d399",
              padding: "2px 8px",
              borderRadius: 9999,
              fontWeight: 700,
              display: "inline-flex",
              alignItems: "center",
              gap: 4
            }}>
              <Sparkles size={11} />
              Gemini 3.5
            </span>
          </h1>

          <p style={{
            color: "#94a3b8",
            fontSize: "0.92rem",
            margin: "0 0 4px 0",
            fontWeight: 500
          }}>
            आपका अपना डिजिटल बिलिंग मुनीम (AI Billing Assistant)
          </p>
          <p style={{
            color: "#64748b",
            fontSize: "0.8rem",
            margin: 0
          }}>
            भारतीय खुदरा दुकानदारों के लिए स्मार्ट GST बिलिंग व स्टॉक मैनेजमेंट
          </p>
        </div>

        {/* Tab Selection */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          padding: "8px",
          background: "rgba(0, 0, 0, 0.25)",
          gap: 6
        }}>
          <button
            type="button"
            onClick={() => { setActiveTab("login"); setErrorMessage(""); }}
            style={{
              padding: "12px",
              borderRadius: 12,
              border: "none",
              background: activeTab === "login" ? "rgba(16, 185, 129, 0.2)" : "transparent",
              color: activeTab === "login" ? "#10b981" : "#94a3b8",
              fontWeight: 700,
              fontSize: "0.92rem",
              cursor: "pointer",
              transition: "all 0.2s ease",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 8,
              borderBottom: activeTab === "login" ? "2px solid #10b981" : "2px solid transparent"
            }}
          >
            <LogIn size={17} />
            <span>लॉग इन (Sign In)</span>
          </button>

          <button
            type="button"
            onClick={() => { setActiveTab("register"); setErrorMessage(""); }}
            style={{
              padding: "12px",
              borderRadius: 12,
              border: "none",
              background: activeTab === "register" ? "rgba(16, 185, 129, 0.2)" : "transparent",
              color: activeTab === "register" ? "#10b981" : "#94a3b8",
              fontWeight: 700,
              fontSize: "0.92rem",
              cursor: "pointer",
              transition: "all 0.2s ease",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 8,
              borderBottom: activeTab === "register" ? "2px solid #10b981" : "2px solid transparent"
            }}
          >
            <UserPlus size={17} />
            <span>नई दुकान जोड़ें (Register)</span>
          </button>
        </div>

        {/* Form Body */}
        <div style={{ padding: "24px 28px 28px" }}>
          {errorMessage && (
            <div style={{
              background: "rgba(239, 68, 68, 0.15)",
              border: "1px solid rgba(239, 68, 68, 0.35)",
              color: "#fca5a5",
              padding: "10px 14px",
              borderRadius: 10,
              fontSize: "0.85rem",
              marginBottom: 18,
              display: "flex",
              alignItems: "center",
              gap: 8
            }}>
              <AlertCircle size={16} style={{ flexShrink: 0 }} />
              <span>{errorMessage}</span>
            </div>
          )}

          {successMessage && (
            <div style={{
              background: "rgba(16, 185, 129, 0.15)",
              border: "1px solid rgba(16, 185, 129, 0.35)",
              color: "#6ee7b7",
              padding: "10px 14px",
              borderRadius: 10,
              fontSize: "0.85rem",
              marginBottom: 18,
              display: "flex",
              alignItems: "center",
              gap: 8
            }}>
              <CheckCircle2 size={16} style={{ flexShrink: 0 }} />
              <span>{successMessage}</span>
            </div>
          )}

          {/* TAB 1: LOGIN FORM */}
          {activeTab === "login" && (
            <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <div>
                <label style={{ display: "block", fontSize: "0.82rem", fontWeight: 600, color: "#cbd5e1", marginBottom: 6 }}>
                  मोबाइल नंबर (Mobile Number)
                </label>
                <div style={{
                  display: "flex",
                  alignItems: "center",
                  background: "rgba(0, 0, 0, 0.35)",
                  border: "1px solid rgba(255, 255, 255, 0.12)",
                  borderRadius: 12,
                  padding: "0 14px",
                  transition: "border 0.2s"
                }}>
                  <Phone size={17} style={{ color: "#10b981", marginRight: 10 }} />
                  <input
                    type="tel"
                    required
                    placeholder="10 डिजिट मोबाइल नंबर (उदा: 7983933436)"
                    value={loginPhone}
                    onChange={(e) => setLoginPhone(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "13px 0",
                      background: "transparent",
                      border: "none",
                      color: "#ffffff",
                      fontSize: "0.95rem",
                      outline: "none"
                    }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.82rem", fontWeight: 600, color: "#cbd5e1", marginBottom: 6 }}>
                  पासवर्ड (Password)
                </label>
                <div style={{
                  display: "flex",
                  alignItems: "center",
                  background: "rgba(0, 0, 0, 0.35)",
                  border: "1px solid rgba(255, 255, 255, 0.12)",
                  borderRadius: 12,
                  padding: "0 14px"
                }}>
                  <Lock size={17} style={{ color: "#10b981", marginRight: 10 }} />
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    placeholder="पासवर्ड दर्ज करें"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "13px 0",
                      background: "transparent",
                      border: "none",
                      color: "#ffffff",
                      fontSize: "0.95rem",
                      outline: "none"
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{
                      background: "none",
                      border: "none",
                      color: "#94a3b8",
                      fontSize: "0.78rem",
                      cursor: "pointer",
                      padding: "4px 8px"
                    }}
                  >
                    {showPassword ? "छिपाएं" : "देखें"}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                style={{
                  marginTop: 8,
                  padding: "14px",
                  borderRadius: 12,
                  border: "none",
                  background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
                  color: "#ffffff",
                  fontSize: "1rem",
                  fontWeight: 800,
                  cursor: isLoading ? "not-allowed" : "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: 8,
                  boxShadow: "0 4px 18px rgba(16, 185, 129, 0.35)",
                  transition: "transform 0.15s, opacity 0.15s",
                  opacity: isLoading ? 0.75 : 1
                }}
              >
                <span>{isLoading ? "प्रवेश हो रहा है..." : "दुकान में प्रवेश करें / Enter Dukaan"}</span>
                <ArrowRight size={18} />
              </button>
            </form>
          )}

          {/* TAB 2: REGISTER FORM */}
          {activeTab === "register" && (
            <form onSubmit={handleRegister} style={{ display: "flex", flexDirection: "column", gap: 13 }}>
              <div>
                <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#cbd5e1", marginBottom: 5 }}>
                  दुकानदार का नाम (Full Name) *
                </label>
                <div style={{ display: "flex", alignItems: "center", background: "rgba(0,0,0,0.35)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 10, padding: "0 12px" }}>
                  <User size={15} style={{ color: "#10b981", marginRight: 8 }} />
                  <input
                    type="text"
                    required
                    placeholder="उदा: रमेश कुमार"
                    value={regData.full_name}
                    onChange={(e) => setRegData({ ...regData, full_name: e.target.value })}
                    style={{ width: "100%", padding: "10px 0", background: "transparent", border: "none", color: "#fff", fontSize: "0.9rem", outline: "none" }}
                  />
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                <div>
                  <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#cbd5e1", marginBottom: 5 }}>
                    मोबाइल नंबर *
                  </label>
                  <div style={{ display: "flex", alignItems: "center", background: "rgba(0,0,0,0.35)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 10, padding: "0 12px" }}>
                    <Phone size={15} style={{ color: "#10b981", marginRight: 8 }} />
                    <input
                      type="tel"
                      required
                      placeholder="10 अंक"
                      value={regData.phone}
                      onChange={(e) => setRegData({ ...regData, phone: e.target.value })}
                      style={{ width: "100%", padding: "10px 0", background: "transparent", border: "none", color: "#fff", fontSize: "0.9rem", outline: "none" }}
                    />
                  </div>
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#cbd5e1", marginBottom: 5 }}>
                    पासवर्ड सेट करें *
                  </label>
                  <div style={{ display: "flex", alignItems: "center", background: "rgba(0,0,0,0.35)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 10, padding: "0 12px" }}>
                    <Lock size={15} style={{ color: "#10b981", marginRight: 8 }} />
                    <input
                      type="password"
                      required
                      placeholder="कम से कम 4 अक्षर"
                      value={regData.password}
                      onChange={(e) => setRegData({ ...regData, password: e.target.value })}
                      style={{ width: "100%", padding: "10px 0", background: "transparent", border: "none", color: "#fff", fontSize: "0.9rem", outline: "none" }}
                    />
                  </div>
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 10 }}>
                <div>
                  <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#cbd5e1", marginBottom: 5 }}>
                    दुकान का नाम (Shop Name) *
                  </label>
                  <div style={{ display: "flex", alignItems: "center", background: "rgba(0,0,0,0.35)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 10, padding: "0 12px" }}>
                    <Store size={15} style={{ color: "#10b981", marginRight: 8 }} />
                    <input
                      type="text"
                      required
                      placeholder="उदा: गुप्ता किराना स्टोर"
                      value={regData.shop_name}
                      onChange={(e) => setRegData({ ...regData, shop_name: e.target.value })}
                      style={{ width: "100%", padding: "10px 0", background: "transparent", border: "none", color: "#fff", fontSize: "0.9rem", outline: "none" }}
                    />
                  </div>
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#cbd5e1", marginBottom: 5 }}>
                    प्रकार (Category)
                  </label>
                  <select
                    value={regData.shop_type}
                    onChange={(e) => setRegData({ ...regData, shop_type: e.target.value })}
                    style={{
                      width: "100%",
                      padding: "10px 12px",
                      background: "rgba(0,0,0,0.45)",
                      border: "1px solid rgba(255,255,255,0.12)",
                      borderRadius: 10,
                      color: "#fff",
                      fontSize: "0.88rem",
                      outline: "none"
                    }}
                  >
                    <option value="kirana">किराना (Grocery)</option>
                    <option value="chemist">मेडिकल स्टोर (Chemist)</option>
                    <option value="hardware">हार्डवेयर (Hardware)</option>
                    <option value="garments">कपड़े (Garments)</option>
                    <option value="electronics">इलेक्ट्रॉनिक्स (Electronics)</option>
                    <option value="restaurant">होटल / रेस्टोरेंट (Food)</option>
                  </select>
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#cbd5e1", marginBottom: 5 }}>
                  दुकान का पता (Address - Optional)
                </label>
                <div style={{ display: "flex", alignItems: "center", background: "rgba(0,0,0,0.35)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 10, padding: "0 12px" }}>
                  <MapPin size={15} style={{ color: "#10b981", marginRight: 8 }} />
                  <input
                    type="text"
                    placeholder="उदा: शॉप #4, मेन मार्केट, दिल्ली"
                    value={regData.address}
                    onChange={(e) => setRegData({ ...regData, address: e.target.value })}
                    style={{ width: "100%", padding: "10px 0", background: "transparent", border: "none", color: "#fff", fontSize: "0.9rem", outline: "none" }}
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                style={{
                  marginTop: 6,
                  padding: "13px",
                  borderRadius: 12,
                  border: "none",
                  background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
                  color: "#ffffff",
                  fontSize: "0.96rem",
                  fontWeight: 800,
                  cursor: isLoading ? "not-allowed" : "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: 8,
                  boxShadow: "0 4px 18px rgba(16, 185, 129, 0.35)"
                }}
              >
                <span>{isLoading ? "खाता बन रहा है..." : "दुकान रजिस्टर करें / Register Dukaan"}</span>
                <ArrowRight size={18} />
              </button>
            </form>
          )}

          {/* Download Android APK Bar */}
          <div style={{
            marginTop: 24,
            paddingTop: 18,
            borderTop: "1px solid rgba(255, 255, 255, 0.08)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: 12
          }}>
            <a
              href={apkUrl}
              download="DukaanAI.apk"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 7,
                fontSize: "0.82rem",
                color: "#38bdf8",
                textDecoration: "none",
                fontWeight: 600,
                background: "rgba(56, 189, 248, 0.1)",
                padding: "6px 12px",
                borderRadius: 8,
                border: "1px solid rgba(56, 189, 248, 0.25)"
              }}
            >
              <Download size={14} />
              <span>📱 Download Android APK</span>
            </a>

            <div style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontSize: "0.76rem",
              color: "#34d399",
              fontWeight: 600
            }}>
              <Database size={12} />
              <span>Aiven Cloud MySQL & Gemini 3.5 AI Active</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
