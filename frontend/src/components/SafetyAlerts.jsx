import React from "react";

const severityRank = (code) => {
  const text = (code || "").toLowerCase();
  if (text.includes("critical") || text.includes("mismatch") || text.includes("guide_asserts")) {
    return 1;
  }
  return 2;
};

const severityLabel = (code) => (severityRank(code) === 1 ? "CRITICAL" : "WARN");
const severityIcon = (code) => (severityRank(code) === 1 ? "🔴" : "🟡");

export function SafetyAlerts({ alerts }) {
  if (!alerts?.length) {
    return null;
  }

  const sorted = [...alerts].sort((a, b) => severityRank(a) - severityRank(b));

  const isSafe = !sorted.some((code) => severityRank(code) === 1);

  return (
    <div className="safety-alerts">
      {!isSafe && <p className="safety-warning-title">⚠️ Hemos detectado posibles problemas en la simplificación; revisa con un profesional.</p>}
      <ul>
        {sorted.map((alert, index) => (
          <li key={`${alert}-${index}`} className={severityRank(alert) === 1 ? "critical" : "warn"}>
            <span className="alert-icon">{severityIcon(alert)}</span>
            <strong>{severityLabel(alert)}</strong> {alert}
          </li>
        ))}
      </ul>
    </div>
  );
}
