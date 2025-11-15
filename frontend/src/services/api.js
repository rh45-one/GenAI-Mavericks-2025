const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function processDocument({ textInput, file }) {
  const formData = new FormData();

  if (textInput?.trim()) {
    formData.append("text", textInput.trim());
  }

  if (file) {
    formData.append("file", file);
  }

  if (![...formData.keys()].length) {
    throw new Error("Provide text or upload a document before submitting.");
  }

  const response = await fetch(`${API_BASE_URL}/process_document`, {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({}));
    throw new Error(errorPayload.detail || "Document processing failed.");
  }

  return response.json();
}
