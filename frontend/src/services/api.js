/**
 * API Service for Indian Retail Billing Agent
 * Connected to Render cloud service: https://dukaanbillai.onrender.com
 */

export const RENDER_CLOUD_URL = "https://dukaanbillai.onrender.com";
export const RENDER_API_BASE = "https://dukaanbillai.onrender.com/api";

export const DEFAULT_ONLINE_URL = "https://dukaanbillai.onrender.com";
export const DEFAULT_LAN_URL = "http://192.168.1.100:8001";
export const DEFAULT_LOCAL_URL = "http://127.0.0.1:8001";

// Auto-resolving API Base: Local Dev (any port) -> localhost:8001; Render Cloud / Hosted -> same origin or RENDER_API_BASE
export function getApiBase() {
  if (typeof window !== "undefined" && window.localStorage) {
    const custom = localStorage.getItem("dukaan_backend_url");
    if (custom && custom.trim()) {
      const trimmed = custom.trim().replace(/\/+$/, "");
      return trimmed.endsWith("/api") ? trimmed : `${trimmed}/api`;
    }
  }

  // 1. Web browser environment:
  if (typeof window !== "undefined" && window.location) {
    const host = window.location.hostname;
    const protocol = window.location.protocol;
    const port = window.location.port;

    // Running on FastAPI port directly (e.g. 8001 or 10000)
    if (port === "8001" || port === "10000") {
      return `${protocol}//${host}:${port}/api`;
    }

    // Localhost or local network dev server (Vite on 5173, 5174, 3000, etc.)
    if (host === "localhost" || host === "127.0.0.1" || host.startsWith("192.168.") || host.startsWith("10.")) {
      return `http://127.0.0.1:8001/api`;
    }

    // Hosted on Render or custom public web domain -> use same origin
    if (host && protocol.startsWith("http")) {
      return `${window.location.origin}/api`;
    }
  }

  // 2. Native Mobile APK (Capacitor Android) -> Render Cloud API Base
  return RENDER_API_BASE;
}

export function setApiBase(url) {
  if (!url || !url.trim()) {
    localStorage.removeItem("dukaan_backend_url");
  } else {
    localStorage.setItem("dukaan_backend_url", url.trim().replace(/\/+$/, ""));
  }
}

// Token storage helpers
export function getStoredToken() {
  return localStorage.getItem("dukaan_auth_token");
}

export function setStoredToken(token) {
  if (token) {
    localStorage.setItem("dukaan_auth_token", token);
  } else {
    localStorage.removeItem("dukaan_auth_token");
  }
}

export function getStoredUser() {
  const u = localStorage.getItem("dukaan_user_profile");
  try {
    return u ? JSON.parse(u) : null;
  } catch {
    return null;
  }
}

export function setStoredUser(user) {
  if (user) {
    localStorage.setItem("dukaan_user_profile", JSON.stringify(user));
  } else {
    localStorage.removeItem("dukaan_user_profile");
  }
}

// Default fetch helper with tunnel bypass headers and Authorization
async function fetchWithBypass(url, options = {}) {
  const token = getStoredToken();
  const headers = {
    ...(options.headers || {}),
    "Bypass-Tunnel-Reminder": "true"
  };
  if (token && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }
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

// --- Shopkeeper Authentication API ---
export async function loginUser(phone, password) {
  const base = getApiBase();
  const res = await fetchWithBypass(`${base}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone, password })
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Login failed");
  }
  setStoredToken(data.token);
  setStoredUser(data.user);
  return data;
}

export async function registerUser(userData) {
  const base = getApiBase();
  const res = await fetchWithBypass(`${base}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(userData)
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Registration failed");
  }
  setStoredToken(data.token);
  setStoredUser(data.user);
  return data;
}

export async function getCurrentUser() {
  const token = getStoredToken();
  if (!token) return null;
  const base = getApiBase();
  try {
    const res = await fetchWithBypass(`${base}/auth/me`);
    if (!res.ok) {
      if (res.status === 401) {
        logoutUser();
      }
      return null;
    }
    const user = await res.json();
    setStoredUser(user);
    return user;
  } catch {
    return getStoredUser();
  }
}

export function logoutUser() {
  localStorage.removeItem("dukaan_auth_token");
  localStorage.removeItem("dukaan_user_profile");
  localStorage.removeItem("dukaan_admin_backup_token");
  localStorage.removeItem("dukaan_admin_backup_user");
}

// --- Super Admin Private API ---
export async function getAdminMetrics() {
  const base = getApiBase();
  const res = await fetchWithBypass(`${base}/admin/metrics`);
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to load admin metrics");
  }
  return await res.json();
}

export async function getAdminShopkeepers() {
  const base = getApiBase();
  const res = await fetchWithBypass(`${base}/admin/shopkeepers`);
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to load shopkeepers");
  }
  return await res.json();
}

export async function getShopkeeperBills(userId) {
  const base = getApiBase();
  const res = await fetchWithBypass(`${base}/admin/shopkeepers/${userId}/bills`);
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to load shopkeeper bills");
  }
  return await res.json();
}

export async function toggleShopkeeperStatus(userId, isActive) {
  const base = getApiBase();
  const res = await fetchWithBypass(`${base}/admin/shopkeepers/${userId}/toggle`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ is_active: isActive })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to update status");
  }
  return await res.json();
}

export async function impersonateShopkeeper(userId) {
  const base = getApiBase();
  // Backup admin token so admin can exit impersonation anytime
  const currentToken = getStoredToken();
  const currentUser = getStoredUser();
  if (currentUser && currentUser.role === "super_admin") {
    localStorage.setItem("dukaan_admin_backup_token", currentToken);
    localStorage.setItem("dukaan_admin_backup_user", JSON.stringify(currentUser));
  }

  const res = await fetchWithBypass(`${base}/admin/impersonate/${userId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" }
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Impersonation failed");
  }

  setStoredToken(data.impersonation_token);
  setStoredUser({
    ...data.target_user,
    is_impersonated: true
  });
  return data;
}

export function exitImpersonation() {
  const backupToken = localStorage.getItem("dukaan_admin_backup_token");
  const backupUser = localStorage.getItem("dukaan_admin_backup_user");
  if (backupToken && backupUser) {
    localStorage.setItem("dukaan_auth_token", backupToken);
    localStorage.setItem("dukaan_user_profile", backupUser);
    localStorage.removeItem("dukaan_admin_backup_token");
    localStorage.removeItem("dukaan_admin_backup_user");
    return JSON.parse(backupUser);
  }
  logoutUser();
  return null;
}

export function isImpersonating() {
  return Boolean(localStorage.getItem("dukaan_admin_backup_token"));
}
