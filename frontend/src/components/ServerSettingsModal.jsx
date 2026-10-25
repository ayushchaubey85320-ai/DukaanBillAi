import React, { useState, useEffect } from "react";
import { 
  getApiBase, 
  setApiBase, 
  pingBackend, 
  DEFAULT_ONLINE_URL, 
  DEFAULT_LAN_URL, 
  DEFAULT_LOCAL_URL 
} from "../services/api";
import { Globe, Wifi, Server, CheckCircle2, AlertCircle, RefreshCw, X, Smartphone } from "lucide-react";

export default function ServerSettingsModal({ isOpen, onClose, onServerChanged }) {
  const [currentUrl, setCurrentUrl] = useState("");
  const [customInput, setCustomInput] = useState("");
  const [pingStatus, setPingStatus] = useState({ testing: false, success: null, latency: null, message: "" });

  useEffect(() => {
    if (isOpen) {
      const active = getApiBase();
      setCurrentUrl(active);
      setCustomInput(active.replace(/\/api\/?$/, ""));
      testCurrent(active);
    }
  }, [isOpen]);

  const testCurrent = async (url) => {
    setPingStatus({ testing: true, success: null, latency: null, message: "Pinging server..." });
    try {
      const res = await pingBackend(url);
      setPingStatus({ 
        testing: false, 
        success: true, 
        latency: res.latency, 
        message: `Connected (${res.latency}ms) - ${res.data.name}` 
      });
    } catch (err) {
      setPingStatus({ 
        testing: false, 
        success: false, 
        latency: null, 
        message: `Connection failed: ${err.message}` 
      });
    }
  };

  const handleSelectPreset = (url) => {
    setCustomInput(url);
    const apiUrl = url.replace(/\/+$/, "") + "/api";
    setCurrentUrl(apiUrl);
    setApiBase(apiUrl);
    testCurrent(apiUrl);
    if (onServerChanged) onServerChanged(apiUrl);
  };

  const handleApplyCustom = () => {
    if (!customInput.trim()) return;
    const apiUrl = customInput.trim().replace(/\/+$/, "") + (customInput.includes("/api") ? "" : "/api");
    setCurrentUrl(apiUrl);
    setApiBase(apiUrl);
    testCurrent(apiUrl);
    if (onServerChanged) onServerChanged(apiUrl);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
      <div className="bg-[#111827] border border-gray-700/80 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5 text-gray-100">
        <div className="flex items-center justify-between border-b border-gray-800 pb-4">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <Server className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Server Connection Settings</h2>
              <p className="text-xs text-gray-400">Configure backend server for Mobile APK and Web</p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Live Status Pill */}
        <div className={`p-3.5 rounded-xl border flex items-center justify-between text-xs font-medium ${
          pingStatus.success 
            ? "bg-emerald-950/30 border-emerald-500/40 text-emerald-300"
            : pingStatus.testing
            ? "bg-amber-950/30 border-amber-500/40 text-amber-300"
            : "bg-rose-950/30 border-rose-500/40 text-rose-300"
        }`}>
          <div className="flex items-center gap-2">
            {pingStatus.testing ? (
              <RefreshCw className="w-4 h-4 animate-spin text-amber-400" />
            ) : pingStatus.success ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-400" />
            )}
            <span>{pingStatus.message || "Ready to connect"}</span>
          </div>
          <button
            onClick={() => testCurrent(currentUrl)}
            disabled={pingStatus.testing}
            className="px-2.5 py-1 bg-white/10 hover:bg-white/20 rounded-md transition text-xs font-semibold"
          >
            Retest
          </button>
        </div>

        {/* Quick Connection Presets */}
        <div className="space-y-2.5">
          <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider">
            Select Connection Mode:
          </label>

          {/* Preset 1: Render Cloud Server (Main) */}
          <button
            type="button"
            onClick={() => handleSelectPreset(DEFAULT_ONLINE_URL)}
            className={`w-full text-left p-3.5 rounded-xl border transition flex items-start gap-3 ${
              currentUrl.includes("onrender.com") || currentUrl.includes("dukaanbillai")
                ? "bg-emerald-950/40 border-emerald-500 text-white"
                : "bg-gray-800/40 border-gray-700/60 hover:bg-gray-800 text-gray-300"
            }`}
          >
            <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400 mt-0.5">
              <Globe className="w-4 h-4" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-white">☁️ Render Cloud Service (Primary Online)</span>
                <span className="text-[10px] bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full font-bold">Main Server</span>
              </div>
              <p className="text-xs text-gray-400 mt-0.5">{DEFAULT_ONLINE_URL}</p>
              <p className="text-[11px] text-gray-500 mt-0.5">High availability cloud server on Render for all devices & APK.</p>
            </div>
          </button>

          {/* Preset 2: Local Wi-Fi */}
          <button
            type="button"
            onClick={() => handleSelectPreset(DEFAULT_LAN_URL)}
            className={`w-full text-left p-3.5 rounded-xl border transition flex items-start gap-3 ${
              currentUrl.includes("192.168.")
                ? "bg-blue-950/40 border-blue-500 text-white"
                : "bg-gray-800/40 border-gray-700/60 hover:bg-gray-800 text-gray-300"
            }`}
          >
            <div className="p-2 rounded-lg bg-blue-500/20 text-blue-400 mt-0.5">
              <Wifi className="w-4 h-4" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-white">📶 Local Shop Wi-Fi</span>
                <span className="text-[10px] bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded-full font-bold">Low Latency</span>
              </div>
              <p className="text-xs text-gray-400 mt-0.5">{DEFAULT_LAN_URL}</p>
              <p className="text-[11px] text-gray-500 mt-0.5">For phone connected to the same shop Wi-Fi router.</p>
            </div>
          </button>

          {/* Preset 3: Localhost */}
          <button
            type="button"
            onClick={() => handleSelectPreset(DEFAULT_LOCAL_URL)}
            className={`w-full text-left p-3 rounded-xl border transition flex items-center gap-3 ${
              currentUrl.includes("127.0.0.1") || currentUrl.includes("localhost")
                ? "bg-purple-950/40 border-purple-500 text-white"
                : "bg-gray-800/40 border-gray-700/60 hover:bg-gray-800 text-gray-300"
            }`}
          >
            <div className="p-2 rounded-lg bg-purple-500/20 text-purple-400">
              <Server className="w-4 h-4" />
            </div>
            <div>
              <span className="text-sm font-semibold text-white">💻 Computer Browser (Localhost)</span>
              <p className="text-xs text-gray-400">{DEFAULT_LOCAL_URL}</p>
            </div>
          </button>
        </div>

        {/* Custom Input */}
        <div className="space-y-2 pt-2 border-t border-gray-800">
          <label className="text-xs font-semibold text-gray-300">Or Custom Server URL / IP:</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={customInput}
              onChange={(e) => setCustomInput(e.target.value)}
              placeholder="https://your-domain.com or http://192.168.1.X:8001"
              className="flex-1 px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-xs text-gray-100 focus:outline-none focus:border-emerald-500"
            />
            <button
              type="button"
              onClick={handleApplyCustom}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold transition"
            >
              Apply
            </button>
          </div>
        </div>

        <div className="pt-2 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2 bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs font-semibold rounded-lg transition"
          >
            Close & Continue
          </button>
        </div>
      </div>
    </div>
  );
}
