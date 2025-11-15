import { useState } from "react";
import { UploadFormPlaceholder } from "./components/UploadFormPlaceholder.jsx";
import { SafetyAlerts } from "./components/SafetyAlerts.jsx";
import { processDocument } from "./services/api.js";

const initialResult = {
  simplified_text: "Submit a document to see Justice Made Clear in action.",
  legal_guide: [],
  original_text: "",
  safety_flags: []
};

const sampleResult = {
  simplified_text:
    "This letter is a standard notice about a missed rent payment. Pay the full balance within 10 days to avoid eviction proceedings.",
  legal_guide: [
    {
      category: "meaningForYou",
      title: "What this means",
      description: "Your landlord says you owe $1,250 covering September rent plus late fees."
    },
    {
      category: "whatToDoNow",
      title: "Immediate steps",
      description: "Pay the amount or contact the landlord to agree on a payment plan before October 15."
    },
    {
      category: "whatHappensNext",
      title: "Next steps",
      description: "If no payment is made, they can file an eviction case after October 20."
    },
    {
      category: "deadlinesAndRisks",
      title: "Deadlines & risks",
      description: "Missing the deadline may result in court fees and eviction."
    }
  ],
  original_text:
    "Notice: You failed to pay the rent due September 1 totaling $1,250. Pay within ten (10) days to cure this default or the tenancy will terminate.",
  safety_flags: ["This document could affect your housing status."]
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
  const [isResultVisible, setIsResultVisible] = useState(false);

  const handleSubmit = async (payload) => {
    setIsLoading(true);
    setErrorMessage("");
    setIsResultVisible(true);
    setResult((previous) => ({
      ...previous,
      simplified_text: "Processing document…"
    }));

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
      setIsResultVisible(false);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setIsResultVisible(false);
    setResult(initialResult);
    setErrorMessage("");
    setIsLoading(false);
  };

  const showHomeState = () => {
    setIsLoading(false);
    setIsResultVisible(false);
    setResult(initialResult);
    setErrorMessage("");
  };

  const showLoadingState = () => {
    setErrorMessage("");
    setIsResultVisible(true);
    setIsLoading(true);
    setResult((previous) => ({
      ...previous,
      simplified_text: "Processing document…"
    }));
  };

  const showOutputState = () => {
    setErrorMessage("");
    setIsResultVisible(true);
    setIsLoading(false);
    setResult(sampleResult);
  };

  return (
    <div className="app-shell">
      <header className="hero-header">
        <div className="hero-content">
          <p className="hero-kicker">Justice Made Clear</p>
          <h1>Type legal text here</h1>
          <p className="hero-subtitle">
            Paste confusing legal language or attach a file to instantly get a friendly summary.
          </p>
          <UploadFormPlaceholder
            onSubmit={handleSubmit}
            isLoading={isLoading}
            resultText={result.simplified_text}
            isResultVisible={isResultVisible}
            onReset={handleReset}
          />
          {errorMessage && <p className="error-text">{errorMessage}</p>}
          {isResultVisible && <SafetyAlerts alerts={result.safety_flags} />}
          <div className="debug-controls">
            <p>Debug screens</p>
            <div className="debug-buttons">
              <button type="button" onClick={showHomeState}>
                Home
              </button>
              <button type="button" onClick={showLoadingState}>
                Loading
              </button>
              <button type="button" onClick={showOutputState}>
                Output
              </button>
            </div>
          </div>
        </div>
      </header>
    </div>
  );
}
