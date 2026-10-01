export const ALLOWED_EXTENSIONS = [
  ".pdf",
  ".docx",
  ".txt",
  ".html",
  ".htm",
  ".csv",
  ".json",
  ".md",
  ".markdown",
];

export const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024; // 50 MB

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function getFileExtension(filename: string): string {
  const parts = filename.split(".");
  if (parts.length <= 1) return "";
  return `.${parts[parts.length - 1]?.toLowerCase()}`;
}

export function validateFile(file: File): { valid: boolean; error?: string } {
  if (file.size === 0) {
    return { valid: false, error: "File is empty (0 bytes)." };
  }

  if (file.size > MAX_FILE_SIZE_BYTES) {
    return {
      valid: false,
      error: `File exceeds maximum limit of 50 MB (${formatFileSize(file.size)}).`,
    };
  }

  const ext = getFileExtension(file.name);
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    return {
      valid: false,
      error: `Format '${ext || "unknown"}' is not supported. Supported: ${ALLOWED_EXTENSIONS.join(", ")}`,
    };
  }

  return { valid: true };
}
