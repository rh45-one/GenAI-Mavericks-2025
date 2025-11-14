import React from "react";

// Placeholder viewer for the original document.
// Props: { documentInput: DocumentInput }
// Displays raw text or renders PDF/image previews once implemented.
// Responsive requirement: original text should remain accessible on phones.
export function DocumentViewerPlaceholder() {
  return (
    <section className="document-viewer-placeholder">
      <h2>Original Document</h2>
      <p>Preview of uploaded document will render here.</p>
    </section>
  );
}
