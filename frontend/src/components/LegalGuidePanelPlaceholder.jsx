import React from "react";

export function LegalGuidePanelPlaceholder({ guide }) {
  if (!guide?.length) {
    return <p>The structured legal guide will appear after processing.</p>;
  }

  return (
    <div className="legal-guide-grid">
      {guide.map((item, index) => (
        <article key={`${item.title}-${index}`} className="legal-guide-card">
          <p className="legal-guide-eyebrow">{item.category}</p>
          <h3>{item.title}</h3>
          <p>{item.description}</p>
        </article>
      ))}
    </div>
  );
}
