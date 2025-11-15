import React, { useEffect, useRef, useState } from "react";

export function UploadFormPlaceholder({ onSubmit, isLoading, resultText, isResultVisible, onReset }) {
  const [textInput, setTextInput] = useState("");
  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState("");
  const hiddenFileInput = useRef(null);
  const hiddenCameraInput = useRef(null);
  const [showAttachmentMenu, setShowAttachmentMenu] = useState(false);

  const handleSubmit = (event) => {
    event.preventDefault();
    if (isResultVisible) {
      onReset?.();
      return;
    }
    setShowAttachmentMenu(false);
    onSubmit?.({ textInput, file });
  };

  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0] || null;
    setFile(selectedFile);
    setFileName(selectedFile?.name || "");
  };

  const openFilePicker = () => {
    setShowAttachmentMenu(false);
    hiddenFileInput.current?.click();
  };

  const openCameraPicker = () => {
    setShowAttachmentMenu(false);
    hiddenCameraInput.current?.click();
  };

  const toggleAttachmentMenu = () => {
    setShowAttachmentMenu((previous) => !previous);
  };

  useEffect(() => {
    if (!isResultVisible) {
      setTextInput("");
      setFile(null);
      setFileName("");
      if (hiddenFileInput.current) {
        hiddenFileInput.current.value = "";
      }
      if (hiddenCameraInput.current) {
        hiddenCameraInput.current.value = "";
      }
      setShowAttachmentMenu(false);
    }
  }, [isResultVisible]);

  return (
    <form className={`hero-form ${isResultVisible ? "is-results" : ""}`} onSubmit={handleSubmit}>
      <div className={`hero-pill ${isResultVisible ? "is-results" : ""}`}>
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
          <>
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
            <div className="hero-plus-wrapper">
              <button
                className={`hero-plus-button ${showAttachmentMenu ? "is-open" : ""}`}
                type="button"
                onClick={toggleAttachmentMenu}
                disabled={isLoading}
                aria-label="Show attachment options"
                aria-expanded={showAttachmentMenu}
              >
                <span aria-hidden="true">+</span>
              </button>
              <div className={`hero-attachment-menu ${showAttachmentMenu ? "is-open" : ""}`}>
                <button
                  className="hero-attachment-button"
                  type="button"
                  onClick={openCameraPicker}
                  disabled={isLoading}
                  aria-label="Scan with camera"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path
                      d="M5 7h2.2l1-1.5h7.6l1 1.5H19a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V9a2 2 0 012-2z"
                      stroke="currentColor"
                      strokeWidth="1.6"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                    <circle cx="12" cy="13" r="3" stroke="currentColor" strokeWidth="1.6" />
                  </svg>
                </button>
                <button
                  className="hero-attachment-button"
                  type="button"
                  onClick={openFilePicker}
                  disabled={isLoading}
                  aria-label="Upload a document"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path
                      d="M12 19V5m0 0l-5 5m5-5 5 5"
                      stroke="currentColor"
                      strokeWidth="1.6"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                    <rect x="4" y="16" width="16" height="4" rx="2" stroke="currentColor" strokeWidth="1.6" />
                  </svg>
                </button>
              </div>
            </div>
          </>
        )}
      </div>
      <input
        ref={hiddenFileInput}
        type="file"
        accept=".pdf,.png,.jpg,.jpeg,.txt"
        className="sr-only"
        onChange={handleFileChange}
      />
      <input
        ref={hiddenCameraInput}
        type="file"
        accept="image/*"
        capture="environment"
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
