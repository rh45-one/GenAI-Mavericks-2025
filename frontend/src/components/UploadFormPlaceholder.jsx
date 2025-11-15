import React, { useEffect, useRef, useState } from "react";

export function UploadFormPlaceholder({ onSubmit, isLoading, resultText, isResultVisible, onReset }) {
  const [textInput, setTextInput] = useState("");
  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState("");
  const hiddenFileInput = useRef(null);

  const handleSubmit = (event) => {
    event.preventDefault();
    if (isResultVisible) {
      onReset?.();
      return;
    }
    onSubmit?.({ textInput, file });
  };

  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0] || null;
    setFile(selectedFile);
    setFileName(selectedFile?.name || "");
  };

  const openFilePicker = () => hiddenFileInput.current?.click();

  useEffect(() => {
    if (!isResultVisible) {
      setTextInput("");
      setFile(null);
      setFileName("");
      if (hiddenFileInput.current) {
        hiddenFileInput.current.value = "";
      }
    }
  }, [isResultVisible]);

  return (
    <form className={`hero-form ${isResultVisible ? "is-results" : ""}`} onSubmit={handleSubmit}>
      <div className={`hero-pill ${isResultVisible ? "is-results" : ""}`}>
        <span className={`hero-icon ${isResultVisible ? "is-results" : ""}`} aria-hidden="true">
          {isResultVisible ? (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M5 12l4 4 10-10"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          ) : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M15 15l5 5m-3-8a7 7 0 11-14 0 7 7 0 0114 0z"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          )}
        </span>

        {isResultVisible ? (
          <div className="hero-result-text">
            <p>{resultText || "Processing document…"}</p>
          </div>
        ) : (
          <input
            className="hero-text-input"
            type="text"
            placeholder="Type legal text here..."
            value={textInput}
            onChange={(event) => setTextInput(event.target.value)}
            disabled={isLoading}
          />
        )}

        {!isResultVisible && (
          <button className="hero-search-button" type="submit" disabled={isLoading} aria-label="Simplify text">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M10 4l8 8-8 8"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        )}

        {!isResultVisible && (
          <button className="hero-plus-button" type="button" onClick={openFilePicker} disabled={isLoading} aria-label="Upload document">
            <span aria-hidden="true">+</span>
          </button>
        )}
      </div>
      <input
        ref={hiddenFileInput}
        type="file"
        accept=".pdf,.png,.jpg,.jpeg,.txt"
        className="sr-only"
        onChange={handleFileChange}
      />
      {!isResultVisible && fileName && <p className="selected-file">Attached: {fileName}</p>}

      {isResultVisible && (
        <div className="hero-actions">
          <button className="hero-secondary-button" type="button" onClick={onReset} disabled={isLoading}>
            Start a new document
          </button>
          <button className="hero-ghost-button" type="button" onClick={openFilePicker} disabled={isLoading}>
            Attach another file
          </button>
        </div>
      )}
    </form>
  );
}
