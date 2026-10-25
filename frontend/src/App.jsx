import React, { useState, useEffect } from "react";
import confetti from "canvas-confetti";
import Navbar from "./components/Navbar";
import ChatInterface from "./components/ChatInterface";
import VoiceController from "./components/VoiceController";
import LiveBillCard from "./components/LiveBillCard";
import BillModal from "./components/BillModal";
import OnboardingModal from "./components/OnboardingModal";
import BillHistory from "./components/BillHistory";
import TestMatrixRunner from "./components/TestMatrixRunner";
import ServerSettingsModal from "./components/ServerSettingsModal";
import AuthModal from "./components/AuthModal";
import SuperAdminPortal from "./components/SuperAdminPortal";
import { 
  sendChatMessage, getCurrentBill, getShopProfile,
  getCurrentUser, logoutUser, isImpersonating, exitImpersonation
} from "./services/api";
import { speechService } from "./services/speech";

export default function App() {
  const [sessionId] = useState(() => "counter_" + Math.random().toString(36).substring(2, 9));
  const [language, setLanguage] = useState("en"); // "en" or "hi"
  const [mobileTab, setMobileTab] = useState("chat"); // "chat" or "receipt"
  const [isOfflineMode, setIsOfflineMode] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [impersonating, setImpersonating] = useState(() => isImpersonating());

  const [shopInfo, setShopInfo] = useState({
    name: "Apna Super Store",
    type: "kirana",
    gstin: "07AAACB1234D1Z5",
    phone: "+91 9876543210",
    address: "Shop #12, Central Market, Delhi - 110001",
    upi_id: "apnastore@upi"
  });

  const [bill, setBill] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeModal, setActiveModal] = useState(null); // "invoice" | "settings" | "server" | "history" | "tests" | "auth" | "admin" | null

  const [messages, setMessages] = useState([
    {
      role: "bot",
      text: "Namaste! Welcome to DukaanAI Billing Assistant. Just speak or type items to generate your bill (e.g. 'Add 2 kg rice at 60 rupees' or '2 packet biscuit 20 each').",
      time: "Just now",
      intent: "greet",
      confidence: 1.0
    }
  ]);

  // Load initial shop profile, bill state, and authenticated user
  useEffect(() => {
    getCurrentUser()
      .then(user => {
        if (user) {
          setCurrentUser(user);
          setImpersonating(isImpersonating());
        }
      })
      .catch(() => {});

    getShopProfile()
      .then(res => {
        if (res) setShopInfo(res);
      })
      .catch(err => console.warn("Could not fetch shop profile:", err));

    getCurrentBill(sessionId)
      .then(res => {
        if (res) setBill(res);
      })
      .catch(err => console.warn("Could not fetch initial bill:", err));
  }, [sessionId]);

  const handleAuthSuccess = (user) => {
    setCurrentUser(user);
    setImpersonating(isImpersonating());
    if (user.role === "super_admin") {
      setActiveModal("admin");
    } else {
      getShopProfile().then(res => res && setShopInfo(res)).catch(() => {});
      getCurrentBill(sessionId).then(res => res && setBill(res)).catch(() => {});
    }
  };

  const handleLogout = () => {
    logoutUser();
    setCurrentUser(null);
    setImpersonating(false);
    getShopProfile().then(res => res && setShopInfo(res)).catch(() => {});
  };

  const handleExitImpersonation = () => {
    const adminUser = exitImpersonation();
    setCurrentUser(adminUser);
    setImpersonating(false);
    setActiveModal("admin");
    getShopProfile().then(res => res && setShopInfo(res)).catch(() => {});
  };

  const handleSendMessage = async (userText) => {
    if (!userText.trim() || isProcessing) return;

    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    // Append user message
    const newMessages = [
      ...messages,
      { role: "user", text: userText, time: timeStr }
    ];
    setMessages(newMessages);
    setIsProcessing(true);

    try {
      const response = await sendChatMessage(sessionId, userText);
      const data = response.data;

      // Update bill and shop info
      if (data.bill) setBill(data.bill);
      if (data.shop_info) setShopInfo(data.shop_info);
      if (data.language) setLanguage(data.language);
      setIsOfflineMode(response.offline || false);

      // Play audio response
      if (data.reply_voice) {
        speechService.speak(data.reply_voice, data.language || language);
      }

      // Append bot response
      setMessages([
        ...newMessages,
        {
          role: "bot",
          text: data.reply,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          intent: data.intent,
          confidence: data.confidence
        }
      ]);

      // If user finalized the bill, trigger celebratory confetti and open invoice modal!
      if (data.intent === "finalize_bill" || data.intent === "print_thermal" || data.intent === "download_pdf") {
        confetti({
          particleCount: 80,
          spread: 60,
          origin: { y: 0.6 }
        });
        setActiveModal("invoice");
      }
    } catch (err) {
      console.error("Chat error:", err);
      setIsOfflineMode(true);
      setMessages([
        ...newMessages,
        {
          role: "bot",
          text: "Network error. Please make sure the backend server is running on port 8001.",
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          intent: "error"
        }
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleToggleLanguage = () => {
    const nextLang = language === "en" ? "hi" : "en";
    setLanguage(nextLang);
    handleSendMessage(nextLang === "hi" ? "Switch to Hindi" : "Switch to English");
  };

  const handleRemoveItem = (itemName) => {
    handleSendMessage(`Remove ${itemName}`);
  };

  const handleChangeQuantity = (itemName, newQty) => {
    handleSendMessage(`${itemName} ${newQty}`);
  };

  const handleResetBill = () => {
    handleSendMessage("Start new bill");
  };

  const handleFinalizeBill = () => {
    handleSendMessage("Print invoice");
  };

  return (
    <div className="app-wrapper">
      {/* Super Admin Impersonation Top Banner */}
      {impersonating && (
        <div style={{
          background: "linear-gradient(90deg, #9a3412, #c2410c, #ea580c)",
          color: "#fff",
          padding: "8px 16px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: "0.82rem",
          fontWeight: 700,
          boxShadow: "0 2px 10px rgba(0,0,0,0.3)"
        }}>
          <span>👑 <strong>SUPER ADMIN IMPERSONATION:</strong> Managing Store <u>{currentUser?.shop_name || "Store"}</u> ({currentUser?.phone}). Actions reflect in live data.</span>
          <button
            onClick={handleExitImpersonation}
            style={{
              background: "#fff",
              color: "#c2410c",
              border: "none",
              borderRadius: 6,
              padding: "4px 12px",
              fontWeight: 800,
              fontSize: "0.78rem",
              cursor: "pointer",
              boxShadow: "0 2px 6px rgba(0,0,0,0.2)"
            }}
          >
            Exit & Return to Super Admin Portal ➔
          </button>
        </div>
      )}

      {/* Top Navbar */}
      <Navbar
        shopInfo={shopInfo}
        language={language}
        currentUser={currentUser}
        onToggleLanguage={handleToggleLanguage}
        onOpenSettings={() => setActiveModal("settings")}
        onOpenServerSettings={() => setActiveModal("server")}
        onOpenHistory={() => setActiveModal("history")}
        onOpenTests={() => setActiveModal("tests")}
        onResetBill={handleResetBill}
        onOpenAuth={() => setActiveModal("auth")}
        onOpenAdmin={() => setActiveModal("admin")}
        onLogout={handleLogout}
      />

      {/* Offline Alert Banner */}
      {isOfflineMode && (
        <div 
          onClick={() => setActiveModal("server")}
          style={{
            background: "linear-gradient(90deg, rgba(239, 68, 68, 0.2), rgba(185, 28, 28, 0.3))",
            borderBottom: "1px solid rgba(239, 68, 68, 0.4)",
            padding: "8px 16px",
            fontSize: "0.78rem",
            color: "#fca5a5",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            cursor: "pointer"
          }}
        >
          <span>⚠️ <strong>Backend Unreachable:</strong> Working from offline cache. Tap here to connect to Online Cloud Server or Local Wi-Fi.</span>
          <span style={{ textDecoration: "underline", fontWeight: 700, color: "#fff", marginLeft: 8 }}>
            Connect ⚙️
          </span>
        </div>
      )}

      {/* Mobile Tab Switcher (< 860px) */}
      <div className="mobile-tab-bar">
        <button
          className={`mobile-tab-btn ${mobileTab === "chat" ? "active" : ""}`}
          onClick={() => setMobileTab("chat")}
        >
          <span>💬 Billing Chat</span>
        </button>
        <button
          className={`mobile-tab-btn ${mobileTab === "receipt" ? "active" : ""}`}
          onClick={() => setMobileTab("receipt")}
        >
          <span>🧾 Receipt ({bill?.items?.length || 0}) • ₹{bill?.grand_total?.toFixed(2) || "0.00"}</span>
        </button>
      </div>

      {/* Main Responsive Layout */}
      <main className="app-layout-grid">
        {/* Left Column: Conversational Voice & Text Chat */}
        <section
          className="glass-panel chat-panel"
          style={{
            display: (mobileTab === "chat" || window.innerWidth >= 860) ? "flex" : "none"
          }}
        >
          <ChatInterface messages={messages} language={language} />
          <VoiceController
            onSendMessage={handleSendMessage}
            isProcessing={isProcessing}
            language={language}
          />
        </section>

        {/* Right Column: Live Interactive GST Receipt Card */}
        <section
          className="receipt-panel"
          style={{
            display: (mobileTab === "receipt" || window.innerWidth >= 860) ? "flex" : "none"
          }}
        >
          <LiveBillCard
            bill={bill}
            onRemoveItem={handleRemoveItem}
            onChangeQuantity={handleChangeQuantity}
            onFinalizeBill={handleFinalizeBill}
            onResetBill={handleResetBill}
          />
        </section>
      </main>

      {/* Modals */}
      {activeModal === "auth" && (
        <AuthModal
          isOpen={true}
          onClose={() => setActiveModal(null)}
          onAuthSuccess={handleAuthSuccess}
        />
      )}

      {activeModal === "admin" && (
        <SuperAdminPortal
          onClose={() => setActiveModal(null)}
          onImpersonateSuccess={(targetUser) => {
            handleAuthSuccess(targetUser);
          }}
        />
      )}

      {activeModal === "invoice" && (
        <BillModal
          bill={bill}
          shopInfo={shopInfo}
          sessionId={sessionId}
          onClose={() => setActiveModal(null)}
          onBillSaved={() => {
            handleResetBill();
          }}
        />
      )}

      {activeModal === "settings" && (
        <OnboardingModal
          shopInfo={shopInfo}
          onClose={() => setActiveModal(null)}
          onUpdated={(updated) => setShopInfo(updated)}
        />
      )}

      {activeModal === "server" && (
        <ServerSettingsModal
          isOpen={true}
          onClose={() => setActiveModal(null)}
          onServerChanged={() => {
            setIsOfflineMode(false);
            // Refresh shop and bill from newly connected server
            getShopProfile().then(res => res && setShopInfo(res)).catch(() => {});
            getCurrentBill(sessionId).then(res => res && setBill(res)).catch(() => {});
          }}
        />
      )}

      {activeModal === "history" && (
        <BillHistory
          onClose={() => setActiveModal(null)}
          onSelectBill={(selected) => {
            setBill(selected);
            setActiveModal("invoice");
          }}
        />
      )}

      {activeModal === "tests" && (
        <TestMatrixRunner onClose={() => setActiveModal(null)} />
      )}
    </div>
  );
}
