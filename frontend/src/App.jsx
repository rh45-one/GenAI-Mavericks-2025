import { useEffect, useState } from "react";
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

const GitHubIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <path
      fillRule="evenodd"
      clipRule="evenodd"
      d="M12 2.25c-5.213 0-9.45 4.317-9.45 9.636 0 4.258 2.703 7.871 6.45 9.15.472.091.64-.208.64-.464 0-.229-.009-.837-.013-1.643-2.621.587-3.173-1.28-3.173-1.28-.43-1.12-1.05-1.419-1.05-1.419-.858-.602.065-.59.065-.59.951.067 1.452 1.002 1.452 1.002.843 1.473 2.214 1.047 2.755.802.086-.633.33-1.048.6-1.289-2.093-.244-4.295-1.042-4.295-4.64 0-1.026.354-1.865.934-2.524-.094-.237-.405-1.2.088-2.503 0 0 .79-.262 2.588 1.006a8.79 8.79 0 0 1 4.72 0c1.798-1.268 2.587-1.006 2.587-1.006.494 1.303.183 2.266.09 2.503.58.659.933 1.498.933 2.523 0 3.608-2.205 4.393-4.304 4.632.338.298.64.888.64 1.794 0 1.295-.012 2.341-.012 2.659 0 .257.166.558.647.463 3.744-1.281 6.444-4.892 6.444-9.15 0-5.319-4.238-9.636-9.45-9.636Z"
      fill="currentColor"
    />
  </svg>
);

const SunIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <circle cx="12" cy="12" r="4.25" stroke="currentColor" strokeWidth="1.5" />
    <path
      d="M12 3v2m0 14v2m7-9h2M3 12h2m12.728-6.728 1.414 1.414M6.858 17.142l1.414-1.414m0-7.456L6.858 6.858m11.314 11.284 1.414-1.414"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
    />
  </svg>
);

const MoonIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <path
      d="M19.75 14.5A7.25 7.25 0 0 1 9.5 4.25a.75.75 0 0 0-.93-.93A8.75 8.75 0 1 0 20.68 15.43a.75.75 0 0 0-.93-.93Z"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

/*
const getInitialThemePreference = () => {
  if (typeof window === "undefined") {
    return { theme: "dark", hasManualTheme: false };
  }

  const storedTheme = window.localStorage.getItem("ui-theme");
  if (storedTheme === "light" || storedTheme === "dark") {
    return { theme: storedTheme, hasManualTheme: true };
  }

  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  return { theme: prefersDark ? "dark" : "light", hasManualTheme: false };
};
*/

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
  /* const [{ theme, hasManualTheme }, setThemePreference] = useState(getInitialThemePreference);
  const isDarkMode = theme === "dark"; */

  useEffect(() => {
    let frameId = null;

    const handlePointerMove = (event) => {
      const xRatio = (event.clientX / window.innerWidth - 0.5) * 2;
      const yRatio = (event.clientY / window.innerHeight - 0.5) * 2;

      if (frameId !== null) {
        return;
      }

      frameId = window.requestAnimationFrame(() => {
        document.documentElement.style.setProperty("--cursor-x", xRatio);
        document.documentElement.style.setProperty("--cursor-y", yRatio);
        frameId = null;
      });
    };

    window.addEventListener("pointermove", handlePointerMove);
    return () => {
      window.removeEventListener("pointermove", handlePointerMove);
      if (frameId !== null) {
        window.cancelAnimationFrame(frameId);
      }
    };
  }, []);

  /*
  useEffect(() => {
    if (typeof document === "undefined") {
      return;
    }
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return undefined;
    }

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = (event) => {
      setThemePreference((previous) => {
        if (previous.hasManualTheme) {
          return previous;
        }
        return {
          theme: event.matches ? "dark" : "light",
          hasManualTheme: false
        };
      });
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, []);

  const toggleTheme = () => {
    setThemePreference((previous) => {
      const nextTheme = previous.theme === "dark" ? "light" : "dark";
      if (typeof window !== "undefined") {
        window.localStorage.setItem("ui-theme", nextTheme);
      }
      return {
        theme: nextTheme,
        hasManualTheme: true
      };
    });
  };
  */

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
        <div className="bg-motion-layer" aria-hidden="true">
          <div className="bg-gradient-base" />
          <div className="bg-gradient-overlay" />
          <div className="bg-gradient-noise" />
          <div className="bg-glow" />
        </div>
        <div className="utility-bar" aria-label="Page actions">
          <a
            className="utility-icon github-link"
            href="https://github.com/rh45-one/GenAI-Mavericks-Challenge"
            target="_blank"
            rel="noreferrer noopener"
            aria-label="Open project repository"
          >
            <GitHubIcon />
          </a>
          {/**
           * Theme toggle temporarily disabled while we refine
           * the permanent palette experience.
           */}
          {false && (
            <button
              type="button"
              className="utility-icon theme-toggle"
              onClick={toggleTheme}
              aria-label="Switch theme"
            >
              <SunIcon />
            </button>
          )}
        </div>
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
