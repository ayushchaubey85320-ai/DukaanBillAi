import React, { useState, useEffect } from "react";
import { CheckCircle2, XCircle, RefreshCw, X, ShieldCheck, Zap } from "lucide-react";
import { getTestScenariosReport } from "../services/api";

export default function TestMatrixRunner({ onClose }) {
  const [report, setReport] = useState(null);
  const [running, setRunning] = useState(false);

  const fetchReport = () => {
    setRunning(true);
    getTestScenariosReport()
      .then(res => setReport(res))
      .catch(err => alert("Test execution error: " + err.message))
      .finally(() => setRunning(false));
  };

  useEffect(() => {
    fetchReport();
  }, []);

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ maxWidth: 740, padding: 22 }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <ShieldCheck size={24} style={{ color: "var(--success)" }} />
            <div>
              <div style={{ fontWeight: 800, fontSize: "1.15rem" }}>
                Scenario Coverage Matrix (21 Indian Retail Scenarios)
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                Automated offline test suite covering all real-world retail edge cases
              </div>
            </div>
          </div>
          <button onClick={onClose} style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer" }}>
            <X size={20} />
          </button>
        </div>

        {/* Stats banner */}
        {report && (
          <div style={{
            background: "linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(30, 58, 138, 0.2))",
            border: "1px solid rgba(16, 185, 129, 0.3)",
            borderRadius: "var(--radius-md)",
            padding: "12px 18px",
            marginBottom: 16,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between"
          }}>
            <div>
              <div style={{ fontSize: "0.75rem", textTransform: "uppercase", color: "var(--success)", fontWeight: 700 }}>
                Test Suite Status
              </div>
              <div style={{ fontSize: "1.2rem", fontWeight: 800, color: "#fff" }}>
                {report.passed_scenarios} of {report.total_scenarios} Scenarios Passed ({report.pass_rate})
              </div>
            </div>

            <button
              onClick={fetchReport}
              disabled={running}
              className="btn-secondary"
              style={{ padding: "6px 12px", fontSize: "0.82rem" }}
            >
              <RefreshCw size={14} className={running ? "animate-spin" : ""} />
              <span>{running ? "Testing..." : "Re-Run All"}</span>
            </button>
          </div>
        )}

        {/* Scenario List */}
        <div style={{ maxHeight: 420, overflowY: "auto", display: "flex", flexDirection: "column", gap: 8 }}>
          {running && !report && (
            <div style={{ textAlign: "center", padding: 40, color: "var(--text-dim)" }}>
              <RefreshCw size={24} className="animate-spin" style={{ margin: "0 auto 10px" }} />
              <div>Running 21 comprehensive test scenarios...</div>
            </div>
          )}

          {report?.results?.map((res, idx) => {
            const isPassed = res.status === "PASSED";
            return (
              <div
                key={idx}
                style={{
                  background: isPassed ? "rgba(16, 185, 129, 0.05)" : "rgba(239, 68, 68, 0.08)",
                  border: `1px solid ${isPassed ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.3)"}`,
                  borderRadius: "var(--radius-sm)",
                  padding: "8px 12px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  fontSize: "0.84rem"
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  {isPassed ? (
                    <CheckCircle2 size={16} style={{ color: "var(--success)", flexShrink: 0 }} />
                  ) : (
                    <XCircle size={16} style={{ color: "var(--danger)", flexShrink: 0 }} />
                  )}
                  <div>
                    <div style={{ fontWeight: 600, color: "#fff" }}>
                      {res.description}
                    </div>
                    {res.error && (
                      <div style={{ fontSize: "0.74rem", color: "var(--danger)", marginTop: 2 }}>
                        Error: {res.error}
                      </div>
                    )}
                  </div>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div style={{
                    fontSize: "0.72rem",
                    color: "var(--text-dim)",
                    display: "flex",
                    alignItems: "center",
                    gap: 3
                  }}>
                    <Zap size={11} />
                    <span>{res.latency_ms}ms</span>
                  </div>
                  <span style={{
                    fontSize: "0.68rem",
                    fontWeight: 700,
                    padding: "2px 6px",
                    borderRadius: 4,
                    background: isPassed ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)",
                    color: isPassed ? "var(--success)" : "var(--danger)"
                  }}>
                    {res.status}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
