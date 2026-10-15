export interface FormatInfo {
  extension: string;
  mime_types: string[];
  description: string;
}

export interface ConvertMetadata {
  size_bytes: number;
  conversion_time_ms: number;
  parallel_chunks?: number;
}

export interface ConvertResponse {
  filename: string;
  original_format: string;
  markdown: string;
  metadata: ConvertMetadata;
}

export interface AsyncJobResponse {
  job_id: string;
  status: "pending" | "splitting" | "processing" | "merging" | "completed" | "failed";
  filename: string;
  extension: string;
  size_bytes: number;
  progress: number;
  message: string;
  chunks_total: number;
  chunks_completed: number;
  markdown?: string | null;
  error?: string | null;
  conversion_time_ms?: number | null;
}

export interface BatchItemResult {
  filename: string;
  status: "success" | "error";
  markdown?: string;
  error?: string;
  metadata?: ConvertMetadata;
}

export interface BatchConvertResponse {
  results: BatchItemResult[];
}

export interface UploadedFileItem {
  id: string;
  file: File;
  name: string;
  size: number;
  format: string;
  status: "idle" | "uploading" | "processing" | "success" | "error";
  progress: number;
  totalChunks?: number;
  processedChunks?: number;
  jobMessage?: string;
  markdown?: string;
  error?: string;
  metadata?: ConvertMetadata;
}

