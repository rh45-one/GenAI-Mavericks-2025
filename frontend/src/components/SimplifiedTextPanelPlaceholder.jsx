import React from "react";

// Placeholder simplified text panel.
// Props: { processedDocument: ProcessedDocument }
// Consumes backend response (simplifiedText) from POST /process_document.
// Ensure layout adapts to small screens with readable typography.
export function SimplifiedTextPanelPlaceholder() {
  return (
    <section className="simplified-text-placeholder">
      <h2>Simplified Explanation</h2>
      <p>Simplified content returned by the backend will appear here.</p>
    </section>
  );
}
