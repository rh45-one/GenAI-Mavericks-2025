import React from "react";

export function LegalGuidePanelPlaceholder({ guide }) {
  if (!guide?.length) {
    return <p>La guía legal aparecerá tras el procesamiento.</p>;
  }

  const get = (category) => guide.find((item) => item.category === category)?.description || "";

  return (
    <div className="legal-guide-structured">
      <section>
        <h2>¿Qué significa esto para ti?</h2>
        <p>{get("meaningForYou")}</p>
      </section>
      <section>
        <h2>Qué puedes hacer ahora</h2>
        <p>{get("whatToDoNow")}</p>
      </section>
      <section>
        <h2>Qué puede pasar después</h2>
        <p>{get("whatHappensNext")}</p>
      </section>
      <section>
        <h2>Plazos y riesgos</h2>
        <p>{get("deadlinesAndRisks")}</p>
      </section>
    </div>
  );
}
