/**
 * API Service for Indian Retail Billing Agent
 * Interacts with FastAPI backend at port 8001 with offline local storage cache.
 */

// Dynamic API Base URL resolver: checks user preference -> online public tunnel -> local network -> localhost
export function getApiBase() {
  const custom = localStorage.getItem("dukaan_backend_url");
  if (custom && custom.trim()) {
    return custom.trim().replace(/\/+$/, "") + (custom.includes("/api") ? "" : "/api");
  }
  // If running in Capacitor native Android app, default to the live online public tunnel
  const isNative = window.Capacitor?.isNativePlatform?.() || 
                   window.location.protocol === "file:" || 
                   (window.location.hostname === "localhost" && window.location.port !== "5174");
  if (isNative) {
    return "https://dukaanai-live.loca.lt/api";
  }
  // Standard web browser running on local dev server
  return "http://127.0.0.1:8001/api";
}

export function setApiBase(url) {
  if (!url) {
    localStorage.removeItem("dukaan_backend_url");
  } else {
    localStorage.setItem("dukaan_backend_url", url.trim().replace(/\/+$/, ""));
  }
}

export const DEFAULT_ONLINE_URL = "https://dukaanai-live.loca.lt";
export const DEFAULT_LAN_URL = "http://192.168.1.14:8001";
export const DEFAULT_LOCAL_URL = "http://127.0.0.1:8001";

// Default fetch helper with tunnel bypass headers
async function fetchWithBypass(url, options = {}) {
  const headers = {
    ...(options.headers || {}),
    "Bypass-Tunnel-Reminder": "true"
  };
  return fetch(url, { ...options, headers });
}

export async function pingBackend(testUrl = null) {
  const base = testUrl ? (testUrl.replace(/\/+$/, "") + (testUrl.includes("/api") ? "" : "/api")) : getApiBase();
  const startTime = Date.now();
  const res = await fetchWithBypass(`${base}/shop`, { signal: AbortSignal.timeout(4000) });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  const latency = Date.now() - startTime;
  return { success: true, latency, data, base };
}

export async function sendChatMessage(sessionId, message) {
  const base = getApiBase();
  try {
    const res = await fetchWithBypass(`${base}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    // Cache latest bill state locally
    if (data.bill) {
      localStorage.setItem(`offline_bill_${sessionId}`, JSON.stringify(data.bill));
    }
    return { data, offline: false };
  } catch (err) {
    console.warn("Backend unavailable, using offline fallback:", err);
    // Offline resilience fallback
    const cachedBill = localStorage.getItem(`offline_bill_${sessionId}`);
    const parsed = cachedBill ? JSON.parse(cachedBill) : { items: [], grand_total: 0.0 };
    return {
      data: {
        reply: "Offline mode: Connection to backend server is paused. Working from local cache.",
        reply_voice: "Offline mode active.",
        intent: "offline_fallback",
        confidence: 1.0,
        bill: parsed,
        shop_info: { name: "Local Offline Store", type: "retail" },
        language: "en"
      },
      offline: true
    };
  }
}

export async function getCurrentBill(sessionId) {
  const base = getApiBase();
  try {
    const res = await fetchWithBypass(`${base}/bill/current/${sessionId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    const cached = localStorage.getItem(`offline_bill_${sessionId}`);
    return cached ? JSON.parse(cached) : null;
  }
}

export async function saveBill(sessionId) {
  const base = getApiBase();
  const res = await fetchWithBypass(`${base}/bill/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId })
  });
  if (!res.ok) throw new Error("Failed to save bill");
  return await res.json();
}

export async function getBillHistory() {
  const base = getApiBase();
  const res = await fetchWithBypass(`${base}/bill/history`);
  if (!res.ok) throw new Error("Failed to fetch bill history");
  return await res.json();
}

export async function getShopProfile() {
  const base = getApiBase();
  const res = await fetchWithBypass(`${base}/shop`);
  if (!res.ok) throw new Error("Failed to fetch shop profile");
  return await res.json();
}

export async function updateShopProfile(profileData) {
  const base = getApiBase();
  const res = await fetchWithBypass(`${base}/shop`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profileData)
  });
  if (!res.ok) throw new Error("Failed to update shop profile");
  return await res.json();
}

export async function getBillQr(sessionId) {
  const base = getApiBase();
  const res = await fetchWithBypass(`${base}/bill/${sessionId}/qr`);
  if (!res.ok) throw new Error("Failed to get UPI QR");
  return await res.json();
}

export async function getThermalReceipt(sessionId, cols = 48) {
  const base = getApiBase();
  const res = await fetchWithBypass(`${base}/bill/${sessionId}/thermal?cols=${cols}`);
  if (!res.ok) throw new Error("Failed to get thermal receipt");
  return await res.json();
}

export function getPdfDownloadUrl(sessionId) {
  const base = getApiBase();
  return `${base}/bill/${sessionId}/pdf`;
}

export async function getTestScenariosReport() {
  const base = getApiBase();
  const res = await fetchWithBypass(`${base}/test-scenarios`);
  if (!res.ok) throw new Error("Failed to run scenario tests");
  return await res.json();
}
