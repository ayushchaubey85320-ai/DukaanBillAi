import React, { useState } from "react";
import { Store, X, Check, AlertCircle } from "lucide-react";
import { updateShopProfile } from "../services/api";

const SHOP_TYPES = [
  { id: "kirana", label: "Kirana / Grocery Store" },
  { id: "pharmacy", label: "Pharmacy / Medical Store" },
  { id: "garments", label: "Garments / Clothing" },
  { id: "restaurant", label: "Restaurant / Cafe / Food" },
  { id: "electronics", label: "Electronics / Electricals" },
  { id: "stationery", label: "Stationery / Books" },
  { id: "dairy", label: "Dairy & Sweets" },
  { id: "hardware", label: "Hardware & Tools" }
];

export default function OnboardingModal({ shopInfo, onClose, onUpdated }) {
  const [formData, setFormData] = useState({
    name: shopInfo?.name || "Apna Super Store",
    type: shopInfo?.type || "kirana",
    gstin: shopInfo?.gstin || "07AAACB1234D1Z5",
    phone: shopInfo?.phone || "+91 9876543210",
    address: shopInfo?.address || "Shop #12, Central Market, Delhi - 110001",
    upi_id: shopInfo?.upi_id || "apnastore@upi"
  });

  const [saving, setSaving] = useState(false);
  const [gstValid, setGstValid] = useState(true);

  const handleGstinChange = (val) => {
    const clean = val.toUpperCase();
    setFormData({ ...formData, gstin: clean });
    const pattern = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/;
    setGstValid(!clean || pattern.test(clean));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await updateShopProfile(formData);
      if (onUpdated) onUpdated(formData);
      onClose();
    } catch (err) {
      alert("Failed to update shop: " + err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ padding: 22 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <Store size={22} style={{ color: "var(--accent)" }} />
            <div>
              <div style={{ fontWeight: 700, fontSize: "1.1rem" }}>Shop Profile & Settings</div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                Configures bill header, GST rates, and UPI payment details
              </div>
            </div>
          </div>
          <button onClick={onClose} style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer" }}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {/* Shop Name */}
          <div>
            <label style={{ display: "block", fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: 4 }}>
              Shop / Business Name
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              style={{
                width: "100%",
                background: "rgba(255, 255, 255, 0.05)",
                border: "1px solid var(--border-glass)",
                borderRadius: "var(--radius-sm)",
                padding: "8px 12px",
                color: "#fff",
                outline: "none"
              }}
            />
          </div>

          {/* Business Type */}
          <div>
            <label style={{ display: "block", fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: 4 }}>
              Business Type
            </label>
            <select
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value })}
              style={{
                width: "100%",
                background: "#1e293b",
                border: "1px solid var(--border-glass)",
                borderRadius: "var(--radius-sm)",
                padding: "8px 12px",
                color: "#fff",
                outline: "none"
              }}
            >
              {SHOP_TYPES.map(st => (
                <option key={st.id} value={st.id}>{st.label}</option>
              ))}
            </select>
          </div>

          {/* GSTIN */}
          <div>
            <label style={{ display: "block", fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: 4 }}>
              GSTIN (15-digit Tax Identifier)
            </label>
            <input
              type="text"
              maxLength={15}
              value={formData.gstin}
              onChange={(e) => handleGstinChange(e.target.value)}
              placeholder="e.g. 07AAACB1234D1Z5"
              style={{
                width: "100%",
                background: "rgba(255, 255, 255, 0.05)",
                border: `1px solid ${gstValid ? "var(--border-glass)" : "var(--danger)"}`,
                borderRadius: "var(--radius-sm)",
                padding: "8px 12px",
                color: "#fff",
                fontFamily: "monospace",
                outline: "none"
              }}
            />
            {!gstValid && (
              <div style={{ fontSize: "0.72rem", color: "var(--danger)", marginTop: 3 }}>
                Invalid GSTIN format (must be 15 alphanumeric characters)
              </div>
            )}
          </div>

          {/* Phone & UPI */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: 4 }}>
                Phone Number
              </label>
              <input
                type="text"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                style={{
                  width: "100%",
                  background: "rgba(255, 255, 255, 0.05)",
                  border: "1px solid var(--border-glass)",
                  borderRadius: "var(--radius-sm)",
                  padding: "8px 12px",
                  color: "#fff",
                  outline: "none"
                }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: 4 }}>
                UPI ID (For QR Payment)
              </label>
              <input
                type="text"
                value={formData.upi_id}
                onChange={(e) => setFormData({ ...formData, upi_id: e.target.value })}
                placeholder="name@upi"
                style={{
                  width: "100%",
                  background: "rgba(255, 255, 255, 0.05)",
                  border: "1px solid var(--border-glass)",
                  borderRadius: "var(--radius-sm)",
                  padding: "8px 12px",
                  color: "#fff",
                  outline: "none"
                }}
              />
            </div>
          </div>

          {/* Address */}
          <div>
            <label style={{ display: "block", fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: 4 }}>
              Shop Address
            </label>
            <input
              type="text"
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              style={{
                width: "100%",
                background: "rgba(255, 255, 255, 0.05)",
                border: "1px solid var(--border-glass)",
                borderRadius: "var(--radius-sm)",
                padding: "8px 12px",
                color: "#fff",
                outline: "none"
              }}
            />
          </div>

          {/* Submit button */}
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 10 }}>
            <button type="button" onClick={onClose} className="btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={saving || !gstValid} className="btn-primary">
              <Check size={16} />
              <span>{saving ? "Saving..." : "Save Settings"}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
