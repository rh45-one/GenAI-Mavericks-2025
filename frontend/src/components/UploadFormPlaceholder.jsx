import React from "react";

// Placeholder upload form component.
// Props: { onSubmit(DocumentInput), isLoading }
// Should call POST /process_document with the selected file or pasted text.
// Must support responsive layout (mobile-first) with drag/drop coming later.
export function UploadFormPlaceholder() {
  // TODO: replace with actual form logic.
  return (
    <div className="upload-form-placeholder">
      <p>Upload form will live here (PDF, image, or text).</p>
    </div>
  );
}
