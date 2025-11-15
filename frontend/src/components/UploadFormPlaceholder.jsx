import React, { useState } from "react";

export function UploadFormPlaceholder({ onSubmit, isLoading }) {
  const [textInput, setTextInput] = useState("");
  const [file, setFile] = useState(null);

  const handleSubmit = (event) => {
    event.preventDefault();
    onSubmit?.({ textInput, file });
  };

  const handleFileChange = (event) => {
    setFile(event.target.files?.[0] || null);
  };

  return (
    <form className="upload-form-placeholder" onSubmit={handleSubmit}>
      <label htmlFor="text-input">Paste text</label>
      <textarea
        id="text-input"
        placeholder="Paste or type legal language that needs simplification"
        value={textInput}
        onChange={(event) => setTextInput(event.target.value)}
      />

      <label htmlFor="file-input">Or upload PDF / image</label>
      <input id="file-input" type="file" accept=".pdf,.png,.jpg,.jpeg,.txt" onChange={handleFileChange} />

      <button className="button-primary" type="submit" disabled={isLoading}>
        {isLoading ? "Processing…" : "Simplify document"}
      </button>
    </form>
  );
}
