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
  status: "processing" | "completed" | "failed";
  filename: string;
  original_format: string;
  total_chunks: number;
  processed_chunks: number;
  progress_pct: number;
  estimated_time_ms?: number;
  message?: string;
  result?: ConvertResponse;
  error?: string;
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

