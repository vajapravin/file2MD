export interface FormatInfo {
  extension: string;
  mime_types: string[];
  description: string;
}

export interface ConvertMetadata {
  size_bytes: number;
  conversion_time_ms: number;
}

export interface ConvertResponse {
  filename: string;
  original_format: string;
  markdown: string;
  metadata: ConvertMetadata;
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
  status: "idle" | "uploading" | "success" | "error";
  progress: number;
  markdown?: string;
  error?: string;
  metadata?: ConvertMetadata;
}
