import React, { useRef, useState } from "react";

export function UploadFormPlaceholder({ onSubmit, isLoading }) {
  const [textInput, setTextInput] = useState("");
  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState("");
  const hiddenFileInput = useRef(null);

  const handleSubmit = (event) => {
    event.preventDefault();
    onSubmit?.({ textInput, file });
  };

  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0] || null;
    setFile(selectedFile);
    setFileName(selectedFile?.name || "");
  };

  const openFilePicker = () => hiddenFileInput.current?.click();

  return (
    <form className="hero-form" onSubmit={handleSubmit}>
      <div className="hero-pill">
        <span className="hero-icon" aria-hidden="true">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M15 15l5 5m-3-8a7 7 0 11-14 0 7 7 0 0114 0z"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </span>
        <input
          className="hero-text-input"
          type="text"
          placeholder="Type legal text here..."
          value={textInput}
          onChange={(event) => setTextInput(event.target.value)}
          disabled={isLoading}
        />
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
        <button className="hero-plus-button" type="button" onClick={openFilePicker} disabled={isLoading} aria-label="Upload document">
          <span aria-hidden="true">+</span>
        </button>
      </div>
      <input
        ref={hiddenFileInput}
        type="file"
        accept=".pdf,.png,.jpg,.jpeg,.txt"
        className="sr-only"
        onChange={handleFileChange}
      />
      {fileName && <p className="selected-file">Attached: {fileName}</p>}
    </form>
  );
}
