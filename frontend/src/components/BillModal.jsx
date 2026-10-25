import React, { useState, useEffect } from "react";
import { X, Download, Printer, Share2, CheckCircle, QrCode, FileText } from "lucide-react";
import { getPdfDownloadUrl, getBillQr, getThermalReceipt, saveBill } from "../services/api";

export default function BillModal({ bill, shopInfo, sessionId, onClose, onBillSaved }) {
  const [activeTab, setActiveTab] = useState("invoice"); // "invoice" | "thermal"
  const [qrData, setQrData] = useState(null);
  const [thermalText, setThermalText] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    // Fetch UPI QR code and Thermal text
    getBillQr(sessionId)
      .then(res => setQrData(res))
      .catch(err => console.warn("Failed to load QR:", err));

    getThermalReceipt(sessionId, 48)
      .then(res => setThermalText(res.receipt_text))
      .catch(err => console.warn("Failed to load thermal text:", err));
  }, [sessionId]);

  const handleDownloadPdf = () => {
    const url = getPdfDownloadUrl(sessionId);
    window.open(url, "_blank");
  };

  const handlePrint = () => {
    window.print();
  };

  const handleWhatsAppShare = () => {
    const itemsList = (bill?.items || []).map(i => `${i.name} (${i.quantity}${i.unit}) - Rs.${i.total_amount}`).join("%0A");
    const text = `*${shopInfo?.name || "Shop Invoice"}*%0AInvoice: ${bill?.bill_id || "INV"}%0ADate: ${bill?.date || ""}%0A----------------------%0A${itemsList}%0A----------------------%0A*Total: Rs.${bill?.grand_total}*%0APay via UPI: ${shopInfo?.upi_id || "shopkeeper@upi"}%0AThank you!`;
    const url = `https://wa.me/?text=${text}`;
    window.open(url, "_blank");
  };

  const handleSaveBill = async () => {
    setIsSaving(true);
    try {
      await saveBill(sessionId);
      setSavedSuccess(true);
      if (onBillSaved) onBillSaved();
      setTimeout(() => {
        onClose();
      }, 1200);
    } catch (err) {
      alert("Error saving bill: " + err.message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ padding: 22 }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <FileText size={22} style={{ color: "var(--accent)" }} />
            <div>
              <div style={{ fontWeight: 700, fontSize: "1.1rem" }}>
                {bill?.bill_id || "Invoice"} • ₹{bill?.grand_total?.toFixed(2)}
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                GST Compliant Indian Retail Invoice
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Tab Buttons */}
        <div style={{ display: "flex", gap: 8, marginBottom: 16, borderBottom: "1px solid var(--border-glass)", paddingBottom: 8 }}>
          <button
            className={`btn-secondary ${activeTab === "invoice" ? "active" : ""}`}
            style={{
              background: activeTab === "invoice" ? "var(--accent)" : "transparent",
              color: activeTab === "invoice" ? "#fff" : "var(--text-muted)",
              padding: "6px 14px",
              fontSize: "0.82rem"
            }}
            onClick={() => setActiveTab("invoice")}
          >
            Tax Invoice View
          </button>
          <button
            className={`btn-secondary ${activeTab === "thermal" ? "active" : ""}`}
            style={{
              background: activeTab === "thermal" ? "var(--accent)" : "transparent",
              color: activeTab === "thermal" ? "#fff" : "var(--text-muted)",
              padding: "6px 14px",
              fontSize: "0.82rem"
            }}
            onClick={() => setActiveTab("thermal")}
          >
            Thermal Receipt (80mm)
          </button>
        </div>

        {/* Invoice View Tab */}
        {activeTab === "invoice" && (
          <div style={{
            background: "#ffffff",
            color: "#0f172a",
            borderRadius: "var(--radius-md)",
            padding: 20,
            fontSize: "0.82rem",
            marginBottom: 16,
            maxHeight: 380,
            overflowY: "auto",
            boxShadow: "inset 0 1px 3px rgba(0,0,0,0.2)"
          }}>
            {/* Invoice Header */}
            <div style={{ textAlign: "center", borderBottom: "1px solid #cbd5e1", paddingBottom: 10, marginBottom: 10 }}>
              <div style={{ fontSize: "1.2rem", fontWeight: 800, color: "#1e3a8a" }}>
                {(shopInfo?.name || "RETAIL STORE").toUpperCase()}
              </div>
              <div style={{ color: "#475569", fontSize: "0.75rem" }}>
                {shopInfo?.address || "Main Market, India"} • Phone: {shopInfo?.phone || "+91 98765 43210"}
              </div>
              <div style={{ fontWeight: 600, fontSize: "0.78rem", marginTop: 2 }}>
                GSTIN: {shopInfo?.gstin || "07AAACB1234D1Z5"} | State: Delhi (07)
              </div>
              <div style={{
                display: "inline-block",
                background: "#e0e7ff",
                color: "#1e1b4b",
                fontWeight: 700,
                fontSize: "0.72rem",
                padding: "2px 8px",
                borderRadius: 4,
                marginTop: 6
              }}>
                TAX INVOICE / कर बीजक
              </div>
            </div>

            {/* Meta */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 12, fontSize: "0.75rem" }}>
              <div>
                <b>Invoice #:</b> {bill?.bill_id || "INV-1001"}<br />
                <b>Date:</b> {bill?.date || "Today"}
              </div>
              <div style={{ textAlign: "right" }}>
                <b>Customer:</b> {bill?.customer_name || "Cash Customer"}<br />
                <b>Contact:</b> {bill?.customer_phone_masked || "N/A"}
              </div>
            </div>

            {/* Table */}
            <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: 12 }}>
              <thead>
                <tr style={{ background: "#f1f5f9", borderBottom: "1px solid #cbd5e1", fontSize: "0.72rem" }}>
                  <th style={{ padding: "4px 6px", textAlign: "left" }}>#</th>
                  <th style={{ padding: "4px 6px", textAlign: "left" }}>Item</th>
                  <th style={{ padding: "4px 6px", textAlign: "left" }}>HSN</th>
                  <th style={{ padding: "4px 6px", textAlign: "center" }}>Qty</th>
                  <th style={{ padding: "4px 6px", textAlign: "right" }}>Rate</th>
                  <th style={{ padding: "4px 6px", textAlign: "right" }}>Tax</th>
                  <th style={{ padding: "4px 6px", textAlign: "right" }}>Total</th>
                </tr>
              </thead>
              <tbody>
                {(bill?.items || []).map((it, idx) => (
                  <tr key={idx} style={{ borderBottom: "1px solid #f1f5f9" }}>
                    <td style={{ padding: "6px" }}>{idx + 1}</td>
                    <td style={{ padding: "6px", fontWeight: 600 }}>{it.name}</td>
                    <td style={{ padding: "6px", color: "#64748b" }}>{it.hsn}</td>
                    <td style={{ padding: "6px", textAlign: "center" }}>{it.quantity} {it.unit}</td>
                    <td style={{ padding: "6px", textAlign: "right" }}>₹{it.rate}</td>
                    <td style={{ padding: "6px", textAlign: "right", color: "#64748b" }}>₹{it.total_tax?.toFixed(2)}</td>
                    <td style={{ padding: "6px", textAlign: "right", fontWeight: 700 }}>₹{it.total_amount?.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Totals & UPI QR */}
            <div style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              borderTop: "1px solid #cbd5e1",
              paddingTop: 10
            }}>
              {qrData?.qr_image_base64 && (
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <img
                    src={qrData.qr_image_base64}
                    alt="UPI QR Code"
                    style={{ width: 68, height: 68, border: "1px solid #cbd5e1", borderRadius: 4 }}
                  />
                  <div style={{ fontSize: "0.7rem", color: "#475569" }}>
                    <b>Scan to Pay</b><br />
                    UPI: {shopInfo?.upi_id || "shopkeeper@upi"}
                  </div>
                </div>
              )}

              <div style={{ textAlign: "right", minWidth: 160 }}>
                <div style={{ color: "#64748b" }}>Subtotal: ₹{bill?.items_subtotal?.toFixed(2)}</div>
                {bill?.discount_applied > 0 && (
                  <div style={{ color: "#16a34a" }}>Discount: -₹{bill?.discount_applied?.toFixed(2)}</div>
                )}
                {bill?.total_tax > 0 && (
                  <div style={{ color: "#64748b" }}>GST (CGST+SGST): ₹{bill?.total_tax?.toFixed(2)}</div>
                )}
                <div style={{ fontSize: "1.1rem", fontWeight: 800, color: "#1e3a8a", marginTop: 4 }}>
                  Total: ₹{bill?.grand_total?.toFixed(2)}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Thermal Receipt Tab */}
        {activeTab === "thermal" && (
          <div style={{
            background: "#1e293b",
            color: "#38bdf8",
            fontFamily: "monospace",
            borderRadius: "var(--radius-md)",
            padding: 16,
            fontSize: "0.78rem",
            marginBottom: 16,
            maxHeight: 380,
            overflowY: "auto",
            whiteSpace: "pre-wrap"
          }}>
            {thermalText || "Formatting thermal receipt..."}
          </div>
        )}

        {/* Action Buttons */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "space-between" }}>
          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={handleDownloadPdf} className="btn-secondary" style={{ padding: "8px 14px" }}>
              <Download size={14} />
              <span>Download PDF</span>
            </button>
            <button onClick={handlePrint} className="btn-secondary" style={{ padding: "8px 14px" }}>
              <Printer size={14} />
              <span>Print</span>
            </button>
            <button onClick={handleWhatsAppShare} className="btn-secondary" style={{ padding: "8px 14px", color: "#22c55e" }}>
              <Share2 size={14} />
              <span>WhatsApp</span>
            </button>
          </div>

          <button
            onClick={handleSaveBill}
            disabled={isSaving || savedSuccess}
            className="btn-primary"
            style={{ padding: "8px 18px" }}
          >
            {savedSuccess ? (
              <>
                <CheckCircle size={15} />
                <span>Saved to DB!</span>
              </>
            ) : (
              <span>Save & Next Customer</span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
