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
  const [{ theme, hasManualTheme }, setThemePreference] = useState(getInitialThemePreference);
  const isDarkMode = theme === "dark";

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
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M12 2C6.48 2 2 6.58 2 12.17c0 4.47 2.87 8.26 6.84 9.6.5.1.68-.22.68-.48 0-.24-.01-.87-.01-1.71-2.78.62-3.37-1.37-3.37-1.37-.46-1.2-1.13-1.52-1.13-1.52-.92-.64.07-.62.07-.62 1.02.07 1.56 1.07 1.56 1.07.9 1.57 2.36 1.12 2.94.86.09-.67.35-1.12.63-1.38-2.22-.26-4.56-1.14-4.56-5.07 0-1.12.39-2.04 1.03-2.76-.1-.26-.45-1.32.1-2.75 0 0 .84-.27 2.75 1.05a9.23 9.23 0 0 1 5 0c1.91-1.32 2.75-1.05 2.75-1.05.55 1.43.2 2.49.1 2.75.64.72 1.03 1.64 1.03 2.76 0 3.94-2.34 4.8-4.57 5.06.36.32.68.94.68 1.9 0 1.37-.01 2.48-.01 2.82 0 .26.18.58.69.48A10.2 10.2 0 0 0 22 12.17C22 6.58 17.52 2 12 2Z"
                stroke="currentColor"
                strokeWidth="1.3"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </a>
          <button
            type="button"
            className="utility-icon theme-toggle"
            onClick={toggleTheme}
            aria-label={`Toggle to ${isDarkMode ? "light" : "dark"} mode`}
          >
            {isDarkMode ? (
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path
                  d="M21 12.75A8.25 8.25 0 0 1 11.25 3a.75.75 0 0 0-.74.6 6.75 6.75 0 0 0 10.64 6.89.75.75 0 0 0-.15-1.23Z"
                  stroke="currentColor"
                  strokeWidth="1.3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            ) : (
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="4.5" stroke="currentColor" strokeWidth="1.3" />
                <path
                  d="M12 4V2.5m0 19V21m7-9h1.5M3.5 12H5m11.95-6.95.95-.95M6.1 17.9l.95-.95m0-8L6.1 6.1m12.8 12.8-.95-.95"
                  stroke="currentColor"
                  strokeWidth="1.3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            )}
          </button>
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
