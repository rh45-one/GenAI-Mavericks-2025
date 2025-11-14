import React from "react";

// Placeholder legal guide panel.
// Props: { guide: LegalGuide, warnings: string[] }
// Renders the four fixed blocks: meaningForYou, whatToDoNow, whatHappensNext, deadlinesAndRisks.
// Frontend only formats data coming from POST /process_document; no legal logic here.
export function LegalGuidePanelPlaceholder() {
  return (
    <section className="legal-guide-placeholder">
      <h2>Legal Guide</h2>
      <ul>
        <li>meaningForYou</li>
        <li>whatToDoNow</li>
        <li>whatHappensNext</li>
        <li>deadlinesAndRisks</li>
      </ul>
      <p>Safety warnings will be presented alongside the guide.</p>
    </section>
  );
}
