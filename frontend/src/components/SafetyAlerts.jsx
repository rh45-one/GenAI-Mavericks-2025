import React from "react";

export function SafetyAlerts({ alerts }) {
  if (!alerts?.length) {
    return null;
  }

  return (
    <div className="safety-alerts">
      <h3>Safety warnings</h3>
      <ul>
        {alerts.map((alert, index) => (
          <li key={`${alert}-${index}`}>{alert}</li>
        ))}
      </ul>
    </div>
  );
}
