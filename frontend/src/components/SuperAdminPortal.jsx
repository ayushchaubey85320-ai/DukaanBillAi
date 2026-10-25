import React, { useState, useEffect } from "react";
import { 
  Shield, Store, Users, Receipt, IndianRupee, TrendingUp, Search, 
  LogIn, Eye, Lock, Unlock, X, RefreshCw, Smartphone, AlertCircle, 
  CheckCircle2, Clock, Calendar, Download, ChevronRight
} from "lucide-react";
import { 
  getAdminMetrics, getAdminShopkeepers, getShopkeeperBills, 
  toggleShopkeeperStatus, impersonateShopkeeper, getApiBase 
} from "../services/api";

export default function SuperAdminPortal({ onClose, onImpersonateSuccess }) {
  const [metrics, setMetrics] = useState(null);
  const [shopkeepers, setShopkeepers] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState("all"); // "all" | "active" | "suspended"
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [successToast, setSuccessToast] = useState("");

  // Inspect specific shopkeeper's bills
  const [inspectingUser, setInspectingUser] = useState(null);
  const [userBills, setUserBills] = useState([]);
  const [loadingBills, setLoadingBills] = useState(false);

  // Load platform analytics and shopkeepers list
  const loadDashboardData = async () => {
    setIsLoading(true);
    setError("");
    try {
      const [m, sk] = await Promise.all([
        getAdminMetrics(),
        getAdminShopkeepers()
      ]);
      setMetrics(m);
      setShopkeepers(sk);
    } catch (err) {
      console.error("Super Admin load error:", err);
      setError(err.message || "Failed to load Super Admin dashboard data. Check authorization.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const handleToggleStatus = async (user) => {
    try {
      const newStatus = !user.is_active;
      await toggleShopkeeperStatus(user.id, newStatus);
      setShopkeepers(prev => prev.map(s => s.id === user.id ? { ...s, is_active: newStatus } : s));
      setSuccessToast(`Account status updated for ${user.shop_name}`);
      setTimeout(() => setSuccessToast(""), 3000);
    } catch (err) {
      alert(err.message || "Failed to toggle status");
    }
  };

  const handleImpersonate = async (user) => {
    if (!confirm(`Are you sure you want to login as "${user.shop_name}" (${user.phone})?`)) return;
    try {
      const res = await impersonateShopkeeper(user.id);
      onImpersonateSuccess(res.target_user);
      onClose();
    } catch (err) {
      alert(err.message || "Failed to impersonate shopkeeper");
    }
  };

  const handleViewBills = async (user) => {
    setInspectingUser(user);
    setLoadingBills(true);
    setUserBills([]);
    try {
      const res = await getShopkeeperBills(user.id);
      setUserBills(res.bills || []);
    } catch (err) {
      alert(err.message || "Failed to load user bills");
    } finally {
      setLoadingBills(false);
    }
  };

  const filteredShopkeepers = shopkeepers.filter(sk => {
    const q = searchQuery.toLowerCase();
    const matchesSearch = (
      sk.shop_name?.toLowerCase().includes(q) ||
      sk.full_name?.toLowerCase().includes(q) ||
      sk.phone?.includes(q)
    );
    if (!matchesSearch) return false;
    if (filterType === "active") return sk.is_active;
    if (filterType === "suspended") return !sk.is_active;
    return true;
  });

  return (
    <div className="modal-backdrop" onClick={onClose} style={{ zIndex: 9998, padding: 16 }}>
      <div 
        className="modal-content glass-card"
        onClick={(e) => e.stopPropagation()}
        style={{
          maxWidth: 1100,
          width: "98%",
          maxHeight: "94vh",
          overflowY: "auto",
          padding: 24,
          borderRadius: 24,
          background: "linear-gradient(145deg, rgba(15, 23, 42, 0.98), rgba(10, 15, 30, 0.98))",
          border: "1px solid rgba(245, 158, 11, 0.3)",
          boxShadow: "0 30px 80px rgba(0, 0, 0, 0.8), 0 0 35px rgba(245, 158, 11, 0.15)"
        }}
      >
        {/* Top Header Bar */}
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
          paddingBottom: 16,
          marginBottom: 20
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{
              width: 44,
              height: 44,
              borderRadius: 12,
              background: "linear-gradient(135deg, #f59e0b, #d97706)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#1e1e1e",
              boxShadow: "0 4px 20px rgba(245, 158, 11, 0.4)"
            }}>
              <Shield size={24} />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <h2 style={{ margin: 0, fontSize: "1.35rem", fontWeight: 800, color: "#fff" }}>
                  Super Admin Master Portal
                </h2>
                <span style={{
                  background: "rgba(245, 158, 11, 0.2)",
                  color: "#fbbf24",
                  fontSize: "0.72rem",
                  fontWeight: 700,
                  padding: "2px 8px",
                  borderRadius: 6,
                  border: "1px solid rgba(245, 158, 11, 0.4)"
                }}>
                  OWNER ONLY
                </span>
              </div>
              <p style={{ margin: "2px 0 0", fontSize: "0.8rem", color: "#94a3b8" }}>
                Real-time tracking of registered stores, platform bills, GMV & 1-click user login
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            {/* Refresh Data */}
            <button
              onClick={loadDashboardData}
              disabled={isLoading}
              style={{
                background: "rgba(255, 255, 255, 0.06)",
                border: "1px solid rgba(255, 255, 255, 0.12)",
                color: "#e2e8f0",
                padding: "8px 14px",
                borderRadius: 10,
                fontSize: "0.8rem",
                fontWeight: 600,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6
              }}
            >
              <RefreshCw size={14} className={isLoading ? "spin" : ""} />
              <span>Refresh</span>
            </button>

            {/* Dedicated Owner APK Download */}
            <a
              href={`${getApiBase()}/download-super-admin-apk`}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                background: "linear-gradient(135deg, #f59e0b, #b45309)",
                border: "none",
                color: "#1e1e1e",
                padding: "8px 14px",
                borderRadius: 10,
                fontSize: "0.8rem",
                fontWeight: 700,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
                textDecoration: "none",
                boxShadow: "0 2px 10px rgba(245, 158, 11, 0.3)"
              }}
              title="Download Dedicated Owner Super Admin APK for Android"
            >
              <Smartphone size={15} />
              <span>Admin APK</span>
            </a>

            {/* Close Button */}
            <button
              onClick={onClose}
              style={{
                background: "rgba(255, 255, 255, 0.08)",
                border: "none",
                borderRadius: "50%",
                width: 36,
                height: 36,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#94a3b8",
                cursor: "pointer"
              }}
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Error or Success Alerts */}
        {error && (
          <div style={{
            background: "rgba(239, 68, 68, 0.15)",
            border: "1px solid rgba(239, 68, 68, 0.35)",
            padding: "12px 16px",
            borderRadius: 12,
            fontSize: "0.85rem",
            color: "#fca5a5",
            marginBottom: 18,
            display: "flex",
            alignItems: "center",
            gap: 10
          }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        {successToast && (
          <div style={{
            background: "rgba(16, 185, 129, 0.15)",
            border: "1px solid rgba(16, 185, 129, 0.35)",
            padding: "12px 16px",
            borderRadius: 12,
            fontSize: "0.85rem",
            color: "#6ee7b7",
            marginBottom: 18,
            display: "flex",
            alignItems: "center",
            gap: 10
          }}>
            <CheckCircle2 size={18} />
            <span>{successToast}</span>
          </div>
        )}

        {/* 1. Global Platform KPI Cards */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: 14,
          marginBottom: 24
        }}>
          {/* Total Shopkeepers */}
          <div style={{
            background: "rgba(255, 255, 255, 0.04)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: 16,
            padding: 16,
            display: "flex",
            alignItems: "center",
            gap: 14
          }}>
            <div style={{
              width: 44,
              height: 44,
              borderRadius: 12,
              background: "rgba(59, 130, 246, 0.15)",
              color: "#60a5fa",
              display: "flex",
              alignItems: "center",
              justifyContent: "center"
            }}>
              <Users size={22} />
            </div>
            <div>
              <div style={{ fontSize: "0.75rem", color: "#94a3b8", fontWeight: 600 }}>Total Shopkeepers</div>
              <div style={{ fontSize: "1.45rem", fontWeight: 800, color: "#fff" }}>
                {metrics?.total_shopkeepers ?? "-"}
              </div>
              <div style={{ fontSize: "0.72rem", color: "#34d399" }}>
                {metrics?.active_shopkeepers ?? "-"} active stores
              </div>
            </div>
          </div>

          {/* Total Bills Generated */}
          <div style={{
            background: "rgba(255, 255, 255, 0.04)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: 16,
            padding: 16,
            display: "flex",
            alignItems: "center",
            gap: 14
          }}>
            <div style={{
              width: 44,
              height: 44,
              borderRadius: 12,
              background: "rgba(16, 185, 129, 0.15)",
              color: "#34d399",
              display: "flex",
              alignItems: "center",
              justifyContent: "center"
            }}>
              <Receipt size={22} />
            </div>
            <div>
              <div style={{ fontSize: "0.75rem", color: "#94a3b8", fontWeight: 600 }}>Total Bills Created</div>
              <div style={{ fontSize: "1.45rem", fontWeight: 800, color: "#fff" }}>
                {metrics?.total_bills_generated ?? "-"}
              </div>
              <div style={{ fontSize: "0.72rem", color: "#94a3b8" }}>
                Across all registered stores
              </div>
            </div>
          </div>

          {/* Total Platform GMV */}
          <div style={{
            background: "rgba(255, 255, 255, 0.04)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: 16,
            padding: 16,
            display: "flex",
            alignItems: "center",
            gap: 14
          }}>
            <div style={{
              width: 44,
              height: 44,
              borderRadius: 12,
              background: "rgba(245, 158, 11, 0.15)",
              color: "#fbbf24",
              display: "flex",
              alignItems: "center",
              justifyContent: "center"
            }}>
              <IndianRupee size={22} />
            </div>
            <div>
              <div style={{ fontSize: "0.75rem", color: "#94a3b8", fontWeight: 600 }}>Platform GMV</div>
              <div style={{ fontSize: "1.45rem", fontWeight: 800, color: "#fbbf24" }}>
                ₹{metrics?.total_platform_gmv?.toLocaleString("en-IN") ?? "0.00"}
              </div>
              <div style={{ fontSize: "0.72rem", color: "#94a3b8" }}>
                Gross customer billing
              </div>
            </div>
          </div>

          {/* Today's Activity */}
          <div style={{
            background: "rgba(255, 255, 255, 0.04)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: 16,
            padding: 16,
            display: "flex",
            alignItems: "center",
            gap: 14
          }}>
            <div style={{
              width: 44,
              height: 44,
              borderRadius: 12,
              background: "rgba(168, 85, 247, 0.15)",
              color: "#c084fc",
              display: "flex",
              alignItems: "center",
              justifyContent: "center"
            }}>
              <TrendingUp size={22} />
            </div>
            <div>
              <div style={{ fontSize: "0.75rem", color: "#94a3b8", fontWeight: 600 }}>Today's Billing (24h)</div>
              <div style={{ fontSize: "1.45rem", fontWeight: 800, color: "#fff" }}>
                {metrics?.today_bills ?? 0} bills
              </div>
              <div style={{ fontSize: "0.72rem", color: "#c084fc" }}>
                ₹{metrics?.today_gmv?.toLocaleString("en-IN") ?? "0.00"}
              </div>
            </div>
          </div>
        </div>

        {/* 2. Shopkeeper Directory & Filter Controls */}
        <div style={{
          background: "rgba(255, 255, 255, 0.02)",
          border: "1px solid rgba(255, 255, 255, 0.07)",
          borderRadius: 18,
          padding: 18
        }}>
          {/* Controls Bar */}
          <div style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: 12,
            marginBottom: 16
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, flex: "1 1 280px", maxWidth: 400 }}>
              <div style={{ position: "relative", width: "100%" }}>
                <Search size={15} style={{ position: "absolute", left: 12, top: 11, color: "#94a3b8" }} />
                <input
                  type="text"
                  placeholder="Search by store name, phone, or owner..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 12px 8px 36px",
                    background: "rgba(255, 255, 255, 0.06)",
                    border: "1px solid rgba(255, 255, 255, 0.12)",
                    borderRadius: 10,
                    color: "#fff",
                    fontSize: "0.85rem",
                    outline: "none"
                  }}
                />
              </div>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: "0.78rem", color: "#94a3b8" }}>Filter:</span>
              {["all", "active", "suspended"].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setFilterType(tab)}
                  style={{
                    padding: "6px 12px",
                    borderRadius: 8,
                    border: "none",
                    fontSize: "0.78rem",
                    fontWeight: 600,
                    textTransform: "capitalize",
                    cursor: "pointer",
                    background: filterType === tab ? "rgba(245, 158, 11, 0.25)" : "rgba(255, 255, 255, 0.05)",
                    color: filterType === tab ? "#fbbf24" : "#94a3b8"
                  }}
                >
                  {tab}
                </button>
              ))}
              <span style={{ fontSize: "0.78rem", color: "#64748b", marginLeft: 6 }}>
                ({filteredShopkeepers.length} stores)
              </span>
            </div>
          </div>

          {/* Shopkeepers Table */}
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.84rem" }}>
              <thead>
                <tr style={{
                  borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
                  textAlign: "left",
                  color: "#94a3b8"
                }}>
                  <th style={{ padding: "10px 12px" }}>Store & Category</th>
                  <th style={{ padding: "10px 12px" }}>Owner & Contact</th>
                  <th style={{ padding: "10px 12px" }}>Created</th>
                  <th style={{ padding: "10px 12px", textAlign: "right" }}>Bills Created</th>
                  <th style={{ padding: "10px 12px", textAlign: "right" }}>Total Revenue</th>
                  <th style={{ padding: "10px 12px", textAlign: "center" }}>Status</th>
                  <th style={{ padding: "10px 12px", textAlign: "center" }}>Master Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredShopkeepers.length === 0 ? (
                  <tr>
                    <td colSpan={7} style={{ padding: 32, textAlign: "center", color: "#64748b" }}>
                      No shopkeepers match your search.
                    </td>
                  </tr>
                ) : (
                  filteredShopkeepers.map((sk) => (
                    <tr 
                      key={sk.id}
                      style={{
                        borderBottom: "1px solid rgba(255, 255, 255, 0.05)",
                        transition: "background 0.2s"
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255, 255, 255, 0.03)"}
                      onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
                    >
                      {/* Store & Category */}
                      <td style={{ padding: "12px 12px" }}>
                        <div style={{ fontWeight: 700, color: "#fff" }}>{sk.shop_name}</div>
                        <span style={{
                          display: "inline-block",
                          marginTop: 3,
                          background: "rgba(59, 130, 246, 0.15)",
                          color: "#60a5fa",
                          fontSize: "0.7rem",
                          padding: "1px 6px",
                          borderRadius: 4,
                          textTransform: "uppercase"
                        }}>
                          {sk.shop_type || "KIRANA"}
                        </span>
                      </td>

                      {/* Owner & Contact */}
                      <td style={{ padding: "12px 12px" }}>
                        <div style={{ color: "#e2e8f0" }}>{sk.full_name}</div>
                        <div style={{ color: "#34d399", fontSize: "0.78rem", fontWeight: 600 }}>{sk.phone}</div>
                      </td>

                      {/* Created Date */}
                      <td style={{ padding: "12px 12px", color: "#94a3b8", fontSize: "0.78rem" }}>
                        <div>{sk.created_date}</div>
                        <div style={{ color: "#64748b" }}>Active: {sk.last_active}</div>
                      </td>

                      {/* Bills Count */}
                      <td style={{ padding: "12px 12px", textAlign: "right" }}>
                        <span style={{
                          background: "rgba(16, 185, 129, 0.12)",
                          color: "#34d399",
                          padding: "3px 8px",
                          borderRadius: 6,
                          fontWeight: 700
                        }}>
                          {sk.total_bills} bills
                        </span>
                      </td>

                      {/* Revenue */}
                      <td style={{ padding: "12px 12px", textAlign: "right", fontWeight: 700, color: "#fbbf24" }}>
                        ₹{sk.total_revenue?.toLocaleString("en-IN") || "0.00"}
                      </td>

                      {/* Status */}
                      <td style={{ padding: "12px 12px", textAlign: "center" }}>
                        <span style={{
                          padding: "3px 8px",
                          borderRadius: 6,
                          fontSize: "0.72rem",
                          fontWeight: 700,
                          background: sk.is_active ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)",
                          color: sk.is_active ? "#34d399" : "#fca5a5",
                          border: `1px solid ${sk.is_active ? "rgba(16, 185, 129, 0.4)" : "rgba(239, 68, 68, 0.4)"}`
                        }}>
                          {sk.is_active ? "ACTIVE" : "SUSPENDED"}
                        </span>
                      </td>

                      {/* Master Actions */}
                      <td style={{ padding: "12px 12px", textAlign: "center" }}>
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}>
                          {/* Impersonate / Login as user */}
                          <button
                            onClick={() => handleImpersonate(sk)}
                            style={{
                              background: "linear-gradient(135deg, #f59e0b, #d97706)",
                              border: "none",
                              borderRadius: 6,
                              padding: "5px 10px",
                              color: "#1e1e1e",
                              fontWeight: 700,
                              fontSize: "0.74rem",
                              cursor: "pointer",
                              display: "flex",
                              alignItems: "center",
                              gap: 4
                            }}
                            title="Login to this shopkeeper's store counter & view live data"
                          >
                            <LogIn size={12} />
                            <span>Login As User</span>
                          </button>

                          {/* View Invoices */}
                          <button
                            onClick={() => handleViewBills(sk)}
                            style={{
                              background: "rgba(255, 255, 255, 0.08)",
                              border: "1px solid rgba(255, 255, 255, 0.15)",
                              borderRadius: 6,
                              padding: "5px 9px",
                              color: "#cbd5e1",
                              fontSize: "0.74rem",
                              cursor: "pointer",
                              display: "flex",
                              alignItems: "center",
                              gap: 4
                            }}
                            title="Inspect bills generated by this shopkeeper"
                          >
                            <Eye size={12} />
                            <span>Bills</span>
                          </button>

                          {/* Toggle Account Status */}
                          <button
                            onClick={() => handleToggleStatus(sk)}
                            style={{
                              background: sk.is_active ? "rgba(239, 68, 68, 0.15)" : "rgba(16, 185, 129, 0.15)",
                              border: "none",
                              borderRadius: 6,
                              padding: "5px 8px",
                              color: sk.is_active ? "#f87171" : "#34d399",
                              fontSize: "0.74rem",
                              cursor: "pointer"
                            }}
                            title={sk.is_active ? "Suspend store account" : "Activate store account"}
                          >
                            {sk.is_active ? <Lock size={12} /> : <Unlock size={12} />}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* 3. Bills Inspector Modal */}
        {inspectingUser && (
          <div 
            className="modal-backdrop"
            onClick={() => setInspectingUser(null)}
            style={{ zIndex: 9999, background: "rgba(0, 0, 0, 0.85)" }}
          >
            <div
              className="modal-content glass-card"
              onClick={(e) => e.stopPropagation()}
              style={{
                maxWidth: 720,
                width: "92%",
                maxHeight: "85vh",
                overflowY: "auto",
                padding: 20,
                borderRadius: 18,
                background: "rgba(15, 23, 42, 0.98)",
                border: "1px solid rgba(255, 255, 255, 0.15)"
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: "1.15rem", fontWeight: 700, color: "#fff" }}>
                    Bills for {inspectingUser.shop_name}
                  </h3>
                  <p style={{ margin: "2px 0 0", fontSize: "0.78rem", color: "#94a3b8" }}>
                    Owner: {inspectingUser.full_name} • Phone: {inspectingUser.phone}
                  </p>
                </div>
                <button
                  onClick={() => setInspectingUser(null)}
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
                  <X size={16} />
                </button>
              </div>

              {loadingBills ? (
                <div style={{ padding: 40, textAlign: "center", color: "#94a3b8" }}>
                  <RefreshCw size={24} className="spin" style={{ margin: "0 auto 10px" }} />
                  <div>Loading bills from database...</div>
                </div>
              ) : userBills.length === 0 ? (
                <div style={{ padding: 30, textAlign: "center", color: "#64748b" }}>
                  This shopkeeper has not saved any finalized bills yet.
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {userBills.map((bill) => (
                    <div
                      key={bill.id}
                      style={{
                        background: "rgba(255, 255, 255, 0.04)",
                        border: "1px solid rgba(255, 255, 255, 0.08)",
                        borderRadius: 12,
                        padding: 14,
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center"
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: 700, color: "#34d399", fontSize: "0.92rem" }}>
                          {bill.bill_number}
                        </div>
                        <div style={{ fontSize: "0.78rem", color: "#cbd5e1", marginTop: 2 }}>
                          Customer: {bill.customer_name} • {bill.items_count} items
                        </div>
                        <div style={{ fontSize: "0.72rem", color: "#94a3b8", marginTop: 2 }}>
                          {bill.date}
                        </div>
                      </div>
                      <div style={{ textAlign: "right" }}>
                        <div style={{ fontSize: "1.1rem", fontWeight: 800, color: "#fbbf24" }}>
                          ₹{bill.grand_total?.toFixed(2)}
                        </div>
                        <div style={{ fontSize: "0.72rem", color: "#94a3b8" }}>
                          Tax: ₹{bill.total_tax?.toFixed(2)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
