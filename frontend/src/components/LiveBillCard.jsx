import React from "react";
import { Receipt, Trash2, Plus, Minus, FileText, ArrowRight, User } from "lucide-react";

export default function LiveBillCard({
  bill,
  onRemoveItem,
  onChangeQuantity,
  onFinalizeBill,
  onResetBill
}) {
  const items = bill?.items || [];
  const grandTotal = bill?.grand_total || 0;
  const subtotal = bill?.items_subtotal || 0;
  const discount = bill?.discount_applied || 0;
  const cgst = bill?.total_cgst || 0;
  const sgst = bill?.total_sgst || 0;
  const roundOff = bill?.round_off || 0;

  return (
    <div className="glass-panel" style={{ display: "flex", flexDirection: "column", height: "100%", width: "100%", minWidth: 0, padding: 14 }}>
      {/* Header */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        borderBottom: "1px solid var(--border-glass)",
        paddingBottom: 12,
        marginBottom: 12
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Receipt size={20} style={{ color: "var(--accent)" }} />
          <div>
            <div style={{ fontWeight: 700, fontSize: "1rem" }}>Current Receipt</div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              {bill?.bill_id || "INV-1001"} • {bill?.date || "Today"}
            </div>
          </div>
        </div>

        {bill?.customer_name && bill?.customer_name !== "Cash Customer" && (
          <div style={{
            fontSize: "0.75rem",
            background: "rgba(30, 58, 138, 0.4)",
            border: "1px solid rgba(59, 130, 246, 0.3)",
            padding: "4px 8px",
            borderRadius: "var(--radius-sm)",
            display: "flex",
            alignItems: "center",
            gap: 4
          }}>
            <User size={12} />
            <span>{bill.customer_name}</span>
          </div>
        )}
      </div>

      {/* Items List */}
      <div style={{ flex: 1, overflowY: "auto", minHeight: 180, marginBottom: 14 }}>
        {items.length === 0 ? (
          <div style={{
            height: "100%",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            color: "var(--text-dim)",
            textAlign: "center",
            padding: 20
          }}>
            <Receipt size={40} style={{ opacity: 0.3, marginBottom: 10 }} />
            <div style={{ fontWeight: 500, fontSize: "0.95rem" }}>Bill is empty</div>
            <div style={{ fontSize: "0.8rem", maxWidth: 220, marginTop: 4 }}>
              Tap the mic and say: <br />
              <i style={{ color: "var(--text-muted)" }}>"2 kg rice at 60 rupees"</i>
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
                    <div style={{ fontWeight: 600 }}>{it.name}</div>
                    <div style={{ fontSize: "0.68rem", color: "var(--text-dim)" }}>
                      HSN: {it.hsn} • GST: {it.gst_rate}%
                    </div>
                  </td>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                      <button
                        onClick={() => onChangeQuantity(it.name, Math.max(1, it.quantity - 1))}
                        style={{
                          background: "rgba(255, 255, 255, 0.08)",
                          border: "none",
                          color: "#fff",
                          width: 20,
                          height: 20,
                          borderRadius: 4,
                          cursor: "pointer",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center"
                        }}
                      >
                        <Minus size={10} />
                      </button>
                      <span style={{ fontSize: "0.82rem", fontWeight: 600, minWidth: 28, textAlign: "center" }}>
                        {it.quantity} {it.unit}
                      </span>
                      <button
                        onClick={() => onChangeQuantity(it.name, it.quantity + 1)}
                        style={{
                          background: "rgba(255, 255, 255, 0.08)",
                          border: "none",
                          color: "#fff",
                          width: 20,
                          height: 20,
                          borderRadius: 4,
                          cursor: "pointer",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center"
                        }}
                      >
                        <Plus size={10} />
                      </button>
                    </div>
                  </td>
                  <td style={{ textAlign: "right", color: "var(--text-muted)" }}>
                    ₹{it.rate}
                  </td>
                  <td style={{ textAlign: "right", fontWeight: 600 }}>
                    ₹{it.total_amount?.toFixed(2)}
                  </td>
                  <td style={{ textAlign: "center" }}>
                    <button
                      onClick={() => onRemoveItem(it.name)}
                      style={{
                        background: "transparent",
                        border: "none",
                        color: "var(--text-dim)",
                        cursor: "pointer",
                        padding: 4
                      }}
                      title="Remove item"
                    >
                      <Trash2 size={13} hover={{ color: "var(--danger)" }} />
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
        background: "rgba(0, 0, 0, 0.25)",
        border: "1px solid var(--border-glass)",
        borderRadius: "var(--radius-md)",
        padding: "10px 14px",
        marginBottom: 14,
        fontSize: "0.84rem"
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
          <span style={{ color: "var(--text-muted)" }}>Subtotal:</span>
          <span>₹{subtotal.toFixed(2)}</span>
        </div>
        {discount > 0 && (
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4, color: "var(--success)" }}>
            <span>Discount:</span>
            <span>- ₹{discount.toFixed(2)}</span>
          </div>
        )}
        {(cgst > 0 || sgst > 0) && (
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4, color: "var(--text-muted)" }}>
            <span>Taxes (CGST + SGST):</span>
            <span>₹{(cgst + sgst).toFixed(2)}</span>
          </div>
        )}
        {roundOff !== 0 && (
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4, color: "var(--text-dim)" }}>
            <span>Round off:</span>
            <span>{roundOff > 0 ? "+" : ""}₹{roundOff.toFixed(2)}</span>
          </div>
        )}
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          borderTop: "1px solid var(--border-glass)",
          paddingTop: 8,
          marginTop: 6,
          fontWeight: 700,
          fontSize: "1.1rem"
        }}>
          <span>Grand Total:</span>
          <span style={{ color: "var(--accent)" }}>₹{grandTotal.toFixed(2)}</span>
        </div>
      </div>

      {/* Action Buttons */}
      <div style={{ display: "flex", gap: 10 }}>
        <button
          onClick={onResetBill}
          disabled={items.length === 0}
          className="btn-secondary"
          style={{ flex: 1, justifyContent: "center" }}
        >
          Clear
        </button>
        <button
          onClick={onFinalizeBill}
          disabled={items.length === 0}
          className="btn-primary"
          style={{ flex: 2, justifyContent: "center" }}
        >
          <FileText size={16} />
          <span>Finalize Bill</span>
          <ArrowRight size={14} />
        </button>
      </div>
    </div>
  );
}
