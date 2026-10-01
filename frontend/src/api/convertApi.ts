import { ConvertResponse, BatchConvertResponse, FormatInfo } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL}/api/v1`
  : "/api/v1";

export async function fetchHealth(): Promise<{ status: string; version: string }> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchSupportedFormats(): Promise<FormatInfo[]> {
  const res = await fetch(`${API_BASE}/formats`);
  if (!res.ok) {
    throw new Error(`Failed to load supported formats: ${res.statusText}`);
  }
  const data = await res.json();
  return data.formats;
}

export async function convertSingleFile(file: File): Promise<ConvertResponse> {
  const formData = new FormData();
  formData.append("file", file, file.name);

  const res = await fetch(`${API_BASE}/convert`, {
    method: "POST",
    body: formData,
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || "File conversion failed.");
  }

  return data as ConvertResponse;
}

export async function convertBatchFiles(files: File[]): Promise<BatchConvertResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file, file.name));

  const res = await fetch(`${API_BASE}/convert/batch`, {
    method: "POST",
    body: formData,
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || "Batch conversion failed.");
  }

  return data as BatchConvertResponse;
}
