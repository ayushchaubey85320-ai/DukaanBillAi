import React, { useState } from "react";
import { Receipt, Trash2, Plus, Minus, FileText, ArrowRight, User, Save, CheckCircle2, AlertCircle } from "lucide-react";
import { saveBill } from "../services/api";

export default function LiveBillCard({
  bill,
  sessionId,
  onRemoveItem,
  onChangeQuantity,
  onFinalizeBill,
  onResetBill,
  onBillSaved
}) {
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState("");

  const items = bill?.items || [];
  const grandTotal = bill?.grand_total || 0;
  const subtotal = bill?.items_subtotal || 0;
  const discount = bill?.discount_applied || 0;
  const cgst = bill?.total_cgst || 0;
  const sgst = bill?.total_sgst || 0;
  const roundOff = bill?.round_off || 0;

  const handleDirectSave = async () => {
    if (!items.length || isSaving) return;
    setIsSaving(true);
    setSaveError("");
    try {
      await saveBill(sessionId);
      setSaveSuccess(true);
      setTimeout(() => {
        setSaveSuccess(false);
        if (onBillSaved) onBillSaved();
      }, 1200);
    } catch (err) {
      setSaveError(err.message || "Failed to save bill to database");
      setTimeout(() => setSaveError(""), 3500);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="glass-panel" style={{ display: "flex", flexDirection: "column", height: "100%", width: "100%", minWidth: 0, padding: 16 }}>
      {/* Header */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        borderBottom: "1px solid var(--border-glass)",
        paddingBottom: 12,
        marginBottom: 12
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 36,
            height: 36,
            borderRadius: "var(--radius-md)",
            background: "rgba(16, 185, 129, 0.15)",
            border: "1px solid rgba(16, 185, 129, 0.3)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "var(--accent)"
          }}>
            <Receipt size={20} />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: "1.05rem" }}>Live Receipt</div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              {bill?.bill_id || "INV-1001"} • {bill?.date || "Today"}
            </div>
          </div>
        </div>

        {bill?.customer_name && bill?.customer_name !== "Cash Customer" && (
          <div style={{
            fontSize: "0.78rem",
            background: "rgba(30, 58, 138, 0.45)",
            border: "1px solid rgba(59, 130, 246, 0.4)",
            padding: "4px 10px",
            borderRadius: "var(--radius-full)",
            display: "flex",
            alignItems: "center",
            gap: 6,
            color: "#93c5fd"
          }}>
            <User size={13} />
            <span style={{ fontWeight: 600 }}>{bill.customer_name}</span>
          </div>
        )}
      </div>

      {/* Items List */}
      <div style={{ flex: 1, overflowY: "auto", minHeight: 180, marginBottom: 12 }}>
        {items.length === 0 ? (
          <div style={{
            height: "100%",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            color: "var(--text-dim)",
            textAlign: "center",
            padding: 24
          }}>
            <div style={{
              width: 56,
              height: 56,
              borderRadius: "50%",
              background: "rgba(255, 255, 255, 0.04)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              marginBottom: 12
            }}>
              <Receipt size={28} style={{ opacity: 0.4 }} />
            </div>
            <div style={{ fontWeight: 600, fontSize: "1rem", color: "#e2e8f0" }}>No items in bill yet</div>
            <div style={{ fontSize: "0.82rem", maxWidth: 240, marginTop: 6, lineHeight: 1.4 }}>
              Tap the microphone and say: <br />
              <i style={{ color: "var(--accent)" }}>"2 kg rice 60 rs, 3 biscuit 20 each"</i>
            </div>
          </div>
        ) : (
          <table className="receipt-table">
            <thead>
              <tr>
                <th>Item</th>
                <th>Qty</th>
                <th style={{ textAlign: "right" }}>Rate</th>
                <th style={{ textAlign: "right" }}>Total</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((it, idx) => (
                <tr key={idx}>
                  <td>
                    <div style={{ fontWeight: 600, color: "#f8fafc" }}>{it.name}</div>
                    <div style={{ fontSize: "0.68rem", color: "var(--text-dim)" }}>
                      HSN: {it.hsn || "9999"} • GST: {it.gst_rate !== undefined && it.gst_rate !== null ? it.gst_rate : 0}%
                    </div>
                  </td>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                      <button
                        onClick={() => onChangeQuantity(it.name, Math.max(1, it.quantity - 1))}
                        style={{
                          background: "rgba(255, 255, 255, 0.08)",
                          border: "none",
                          width: 22,
                          height: 22,
                          borderRadius: 4,
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          color: "#fff",
                          cursor: "pointer"
                        }}
                      >
                        <Minus size={11} />
                      </button>
                      <span style={{ fontSize: "0.85rem", minWidth: 28, textAlign: "center", fontWeight: 600 }}>
                        {it.quantity}{it.unit ? ` ${it.unit}` : ""}
                      </span>
                      <button
                        onClick={() => onChangeQuantity(it.name, it.quantity + 1)}
                        style={{
                          background: "rgba(255, 255, 255, 0.08)",
                          border: "none",
                          width: 22,
                          height: 22,
                          borderRadius: 4,
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          color: "#fff",
                          cursor: "pointer"
                        }}
                      >
                        <Plus size={11} />
                      </button>
                    </div>
                  </td>
                  <td style={{ textAlign: "right", fontSize: "0.85rem", color: "var(--text-muted)" }}>
                    ₹{Number(it.rate).toFixed(2)}
                  </td>
                  <td style={{ textAlign: "right", fontWeight: 700, fontSize: "0.9rem", color: "#f8fafc" }}>
                    ₹{Number(it.total_amount || (it.rate * it.quantity)).toFixed(2)}
                  </td>
                  <td style={{ textAlign: "center" }}>
                    <button
                      onClick={() => onRemoveItem(it.name)}
                      style={{
                        background: "transparent",
                        border: "none",
                        color: "var(--text-dim)",
                        cursor: "pointer",
                        padding: 4,
                        transition: "color 0.2s"
                      }}
                      title="Remove item"
                      onMouseEnter={(e) => e.currentTarget.style.color = "var(--danger)"}
                      onMouseLeave={(e) => e.currentTarget.style.color = "var(--text-dim)"}
                    >
                      <Trash2 size={13} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Bill Calculation Summary */}
      <div style={{
        background: "rgba(0, 0, 0, 0.3)",
        border: "1px solid var(--border-glass)",
        borderRadius: "var(--radius-md)",
        padding: "10px 14px",
        marginBottom: 12,
        fontSize: "0.84rem"
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
          <span style={{ color: "var(--text-muted)" }}>Subtotal:</span>
          <span style={{ fontWeight: 500 }}>₹{subtotal.toFixed(2)}</span>
        </div>
        {discount > 0 && (
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4, color: "var(--success)" }}>
            <span>Discount Applied:</span>
            <span style={{ fontWeight: 600 }}>- ₹{discount.toFixed(2)}</span>
          </div>
        )}
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4, color: (cgst + sgst) > 0 ? "var(--text-muted)" : "#34d399" }}>
          <span>GST Tax:</span>
          <span>{(cgst + sgst) > 0 ? `₹${(cgst + sgst).toFixed(2)}` : "₹0.00 (0% Tax)"}</span>
        </div>
        {roundOff !== 0 && (
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4, color: "var(--text-dim)" }}>
            <span>Round off:</span>
            <span>{roundOff > 0 ? "+" : ""}₹{roundOff.toFixed(2)}</span>
          </div>
        )}
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderTop: "1px solid var(--border-glass)",
          paddingTop: 8,
          marginTop: 6
        }}>
          <span style={{ fontWeight: 700, fontSize: "1rem" }}>Grand Total:</span>
          <span style={{ fontWeight: 800, fontSize: "1.25rem", color: "var(--accent)" }}>
            ₹{grandTotal.toFixed(2)}
          </span>
        </div>
      </div>

      {/* Save Success / Error Alerts */}
      {saveSuccess && (
        <div style={{
          background: "rgba(16, 185, 129, 0.2)",
          border: "1px solid rgba(16, 185, 129, 0.5)",
          color: "#6ee7b7",
          padding: "6px 12px",
          borderRadius: "var(--radius-sm)",
          fontSize: "0.8rem",
          display: "flex",
          alignItems: "center",
          gap: 6,
          marginBottom: 10
        }}>
          <CheckCircle2 size={14} />
          <span>Bill #{bill?.bill_id} successfully saved to MySQL database!</span>
        </div>
      )}

      {saveError && (
        <div style={{
          background: "rgba(239, 68, 68, 0.2)",
          border: "1px solid rgba(239, 68, 68, 0.5)",
          color: "#fca5a5",
          padding: "6px 12px",
          borderRadius: "var(--radius-sm)",
          fontSize: "0.8rem",
          display: "flex",
          alignItems: "center",
          gap: 6,
          marginBottom: 10
        }}>
          <AlertCircle size={14} />
          <span>{saveError}</span>
        </div>
      )}

      {/* Action Buttons Row */}
      <div style={{ display: "flex", gap: 8 }}>
        <button
          onClick={onResetBill}
          disabled={items.length === 0}
          className="btn-secondary"
          style={{ flex: 1, justifyContent: "center", padding: "8px 10px", fontSize: "0.84rem" }}
          title="Reset current receipt"
        >
          Clear
        </button>

        <button
          onClick={handleDirectSave}
          disabled={items.length === 0 || isSaving}
          className="btn-secondary"
          style={{
            flex: 1.3,
            justifyContent: "center",
            padding: "8px 10px",
            fontSize: "0.84rem",
            background: "rgba(16, 185, 129, 0.15)",
            border: "1px solid rgba(16, 185, 129, 0.4)",
            color: "#6ee7b7"
          }}
          title="Save bill directly to cloud database"
        >
          <Save size={14} />
          <span>{isSaving ? "Saving..." : "Save Bill"}</span>
        </button>

        <button
          onClick={onFinalizeBill}
          disabled={items.length === 0}
          className="btn-primary"
          style={{ flex: 2, justifyContent: "center", padding: "8px 12px", fontSize: "0.84rem" }}
        >
          <FileText size={15} />
          <span>Invoice & Pay</span>
          <ArrowRight size={13} />
        </button>
      </div>
    </div>
  );
}
