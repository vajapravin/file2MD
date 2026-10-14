import { ConvertResponse, BatchConvertResponse, FormatInfo, AsyncJobResponse } from "../types";

// Default to relative "/api/v1" so it works across both local development and production domains
const API_BASE = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL.replace(/\/$/, "")}/api/v1`
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

export async function fetchJobStatus(jobId: string): Promise<AsyncJobResponse> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch job status (${res.statusText})`);
  }
  return res.json();
}

export async function convertSingleFile(
  file: File,
  onProgress?: (job: AsyncJobResponse) => void
): Promise<ConvertResponse> {
  const formData = new FormData();
  formData.append("file", file, file.name);

  const res = await fetch(`${API_BASE}/convert`, {
    method: "POST",
    body: formData,
  });

  const data = await res.json();

  if (res.status === 202) {
    // Large file queued for parallel chunking: poll until finished
    const initialJob = data as AsyncJobResponse;
    onProgress?.(initialJob);

    const pollIntervalMs = 800;
    const maxAttempts = 600; // ~8 minutes limit

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
      const job = await fetchJobStatus(initialJob.job_id);
      onProgress?.(job);

      if (job.status === "completed") {
        if (job.result) {
          return job.result;
        }
        throw new Error("Parallel conversion completed but no output was found.");
      }

      if (job.status === "failed") {
        throw new Error(job.error || "Parallel chunk conversion failed.");
      }
    }

    throw new Error("Parallel conversion timed out. Please try again.");
  }

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
