const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const IMAGE_EXTENSIONS = ["png", "jpg", "jpeg", "gif", "bmp", "tiff", "tif", "webp", "heic", "heif"];

export async function processDocument({ textInput, file }) {
  const formData = new FormData();
  let sourceType = null;

  const trimmedText = textInput?.trim();
  if (trimmedText) {
    formData.append("plainText", trimmedText);
    sourceType = "text";
  }

  if (file) {
    const detectedType = detectSourceType(file);
    if (!detectedType) {
      throw new Error("Por ahora solo se admiten archivos PDF o imágenes.");
    }

    formData.append("file", file);
    sourceType = detectedType;
  }

  if (!sourceType) {
    throw new Error("Escribe texto o sube un documento antes de enviar.");
  }

  formData.append("sourceType", sourceType);

  const response = await fetch(`${API_BASE_URL}/process_document`, {
    method: "POST",
    body: formData
  });

  let payload = null;
  try {
    payload = await response.json();
  } catch (error) {
    // Keep payload as null if the backend didn't send JSON (e.g., server error)
  }

  if (!response.ok) {
  const message = extractErrorMessage(payload) || "El procesamiento del documento falló.";
    throw new Error(message);
  }

  return payload;
}

function detectSourceType(file) {
  const mimeType = (file.type || "").toLowerCase();
  if (mimeType.includes("pdf")) {
    return "pdf";
  }
  if (mimeType.startsWith("image/")) {
    return "image";
  }

  const extension = (file.name?.split(".").pop() || "").toLowerCase();
  if (extension === "pdf") {
    return "pdf";
  }
  if (IMAGE_EXTENSIONS.includes(extension)) {
    return "image";
  }

  return null;
}

function extractErrorMessage(payload) {
  if (!payload) {
    return "";
  }

  if (typeof payload.detail === "string") {
    return payload.detail;
  }

  if (Array.isArray(payload.detail) && payload.detail.length) {
    const first = payload.detail[0];
    if (typeof first === "string") {
      return first;
    }
    if (first?.msg) {
      return first.msg;
    }
  }

  return "";
}
