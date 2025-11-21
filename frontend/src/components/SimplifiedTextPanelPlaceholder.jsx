import React from "react";

export function SimplifiedTextPanelPlaceholder({ result, isLoading }) {
  if (isLoading) {
    return <p>Procesando documento.</p>;
  }

  const header = result?.header_summary || {};
  const parties = result?.parties_summary || {};
  const fallo = result?.decision_fallo || {};

  return (
    <div className="simplified-sections">
      <section>
        <h2>Datos del caso</h2>
        <p>Tribunal: {header.court || "-"}</p>
        <p>Fecha: {header.date || "-"}</p>
        <p>Número de caso: {header.caseNumber || "-"}</p>
        <p>Número de resolución: {header.resolutionNumber || "-"}</p>
        <p>Tipo de procedimiento: {header.procedureType || "-"}</p>
        <p>Jueza/Juez: {header.judge || "-"}</p>
      </section>

      <section>
        <h2>Partes involucradas</h2>
        <p>Demandante: {parties.plaintiff || "-"}</p>
        {parties.plaintiffRepresentatives && <p>Representantes: {parties.plaintiffRepresentatives}</p>}
        <p>Demandado: {parties.defendant || "-"}</p>
        {parties.defendantRepresentatives && <p>Representantes: {parties.defendantRepresentatives}</p>}
      </section>

      <section>
        <h2>Contexto procesal</h2>
        <p>{result?.procedural_context || result?.proceduralContext || "No hay contexto procesal disponible."}</p>
      </section>

      <section>
        <h2>Resultado del caso (según el FALLO)</h2>
        <p>Quién gana: {fallo.whoWins || "desconocido"}</p>
        <p>Costas: {fallo.costs || "desconocido"}</p>
        <p>Resumen: {fallo.plainText || result?.simplified_text || "-"}</p>
        {fallo.falloLiteral && (
          <div>
            <h3>Fallo literal</h3>
            <pre>{fallo.falloLiteral}</pre>
          </div>
        )}
      </section>
    </div>
  );
}
