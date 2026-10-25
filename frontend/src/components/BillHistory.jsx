import React, { useState, useEffect } from "react";
import { History, X, Search, FileText, ArrowRight } from "lucide-react";
import { getBillHistory } from "../services/api";

export default function BillHistory({ onClose, onSelectBill }) {
  const [bills, setBills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    getBillHistory()
      .then(res => setBills(res))
      .catch(err => console.error("Error loading bills:", err))
      .finally(() => setLoading(false));
  }, []);

  const filteredBills = bills.filter(b =>
    (b.bill_number?.toLowerCase() || "").includes(searchTerm.toLowerCase()) ||
    (b.customer_name?.toLowerCase() || "").includes(searchTerm.toLowerCase())
  );

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ padding: 22 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <History size={22} style={{ color: "var(--accent)" }} />
            <div>
              <div style={{ fontWeight: 700, fontSize: "1.1rem" }}>Past Invoices History</div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                Saved customer bills stored in local SQLite database
              </div>
            </div>
          </div>
          <button onClick={onClose} style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer" }}>
            <X size={20} />
          </button>
        </div>

        {/* Search */}
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          background: "rgba(255, 255, 255, 0.05)",
          border: "1px solid var(--border-glass)",
          borderRadius: "var(--radius-md)",
          padding: "6px 12px",
          marginBottom: 14
        }}>
          <Search size={16} style={{ color: "var(--text-dim)" }} />
          <input
            type="text"
            placeholder="Search by invoice number or customer name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              background: "transparent",
              border: "none",
              outline: "none",
              color: "#fff",
              fontSize: "0.88rem",
              width: "100%"
            }}
          />
        </div>

        {/* List */}
        <div style={{ maxHeight: 380, overflowY: "auto" }}>
          {loading ? (
            <div style={{ textAlign: "center", padding: 30, color: "var(--text-dim)" }}>
              Loading bills history...
            </div>
          ) : filteredBills.length === 0 ? (
            <div style={{ textAlign: "center", padding: 30, color: "var(--text-dim)" }}>
              No bills found.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {filteredBills.map((b) => (
                <div
                  key={b.id}
                  style={{
                    background: "rgba(30, 41, 59, 0.5)",
                    border: "1px solid var(--border-glass)",
                    borderRadius: "var(--radius-md)",
                    padding: "10px 14px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    transition: "all 0.2s ease"
                  }}
                >
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ fontWeight: 700, fontSize: "0.95rem", color: "#fff" }}>
                        {b.bill_number}
                      </span>
                      <span style={{
                        fontSize: "0.72rem",
                        background: "rgba(255, 255, 255, 0.08)",
                        padding: "2px 6px",
                        borderRadius: 4,
                        color: "var(--text-muted)"
                      }}>
                        {b.customer_name}
                      </span>
                    </div>
                    <div style={{ fontSize: "0.74rem", color: "var(--text-dim)", marginTop: 2 }}>
                      {b.date} • {b.items_count} items
                    </div>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <div style={{ textAlign: "right" }}>
                      <div style={{ fontWeight: 700, fontSize: "1.05rem", color: "var(--accent)" }}>
                        ₹{b.grand_total?.toFixed(2)}
                      </div>
                      <div style={{ fontSize: "0.7rem", color: "var(--text-dim)" }}>
                        Tax: ₹{b.total_tax?.toFixed(2)}
                      </div>
                    </div>

                    <button
                      onClick={() => onSelectBill(b)}
                      className="btn-secondary"
                      style={{ padding: "6px 10px" }}
                      title="View bill"
                    >
                      <ArrowRight size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
