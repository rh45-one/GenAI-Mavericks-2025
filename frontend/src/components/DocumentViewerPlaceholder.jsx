import React from "react";

// Placeholder viewer for the original document.
// Props: { documentInput: DocumentInput }
// Displays raw text or renders PDF/image previews once implemented.
// Responsive requirement: original text should remain accessible on phones.
export function DocumentViewerPlaceholder({ text }) {
  if (!text?.trim()) {
    return <p>El texto original aparecerá después del procesamiento.</p>;
  }

  return <div className="document-viewer">{text}</div>;
}
