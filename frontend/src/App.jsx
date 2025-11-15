import { useState } from "react";
import { UploadFormPlaceholder } from "./components/UploadFormPlaceholder.jsx";
import { SimplifiedTextPanelPlaceholder } from "./components/SimplifiedTextPanelPlaceholder.jsx";
import { LegalGuidePanelPlaceholder } from "./components/LegalGuidePanelPlaceholder.jsx";
import { DocumentViewerPlaceholder } from "./components/DocumentViewerPlaceholder.jsx";
import { SafetyAlerts } from "./components/SafetyAlerts.jsx";
import { processDocument } from "./services/api.js";

const initialResult = {
  simplified_text: "Submit a document to see Justice Made Clear in action.",
  legal_guide: [],
  original_text: "",
  safety_flags: []
};

const normalizeLegalGuide = (guidePayload) => {
  if (Array.isArray(guidePayload)) {
    return guidePayload;
  }

  if (guidePayload && typeof guidePayload === "object") {
    return Object.entries(guidePayload).map(([key, value]) => ({
      category: key,
      title: value?.title || key.replace(/([A-Z])/g, " $1").trim(),
      description:
        typeof value === "string"
          ? value
          : value?.description || "More details coming soon."
    }));
  }

  return [];
};

export default function App() {
  const [result, setResult] = useState(initialResult);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const handleSubmit = async (payload) => {
    setIsLoading(true);
    setErrorMessage("");

    try {
      const apiResult = await processDocument(payload);
      setResult({
        simplified_text: apiResult.simplified_text || initialResult.simplified_text,
        legal_guide: normalizeLegalGuide(apiResult.legal_guide),
        original_text: apiResult.original_text || payload.textInput || "",
        safety_flags: apiResult.safety_flags || []
      });
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <header>
        <h1>Justice Made Clear</h1>
        <p>Upload any legal document to get a friendly explanation and practical guidance.</p>
      </header>

      <main>
        <section className="panel">
          <h2>Upload</h2>
          <UploadFormPlaceholder onSubmit={handleSubmit} isLoading={isLoading} />
          {errorMessage && <p className="error-text">{errorMessage}</p>}
          <SafetyAlerts alerts={result.safety_flags} />
        </section>

        <section className="panel">
          <h2>Simplified Explanation</h2>
          <SimplifiedTextPanelPlaceholder text={result.simplified_text} isLoading={isLoading} />
        </section>

        <section className="panel">
          <h2>Legal Guide</h2>
          <LegalGuidePanelPlaceholder guide={result.legal_guide} />
        </section>

        <section className="panel">
          <h2>Original Document</h2>
          <DocumentViewerPlaceholder text={result.original_text} />
        </section>
      </main>
    </div>
  );
}
