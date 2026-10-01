import React, { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { validateFile } from "../utils/fileValidation";

interface FileUploadProps {
  onFilesSelected: (files: File[]) => void;
  onError: (msg: string) => void;
  isProcessing: boolean;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  onFilesSelected,
  onError,
  isProcessing,
}) => {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;

      const validFiles: File[] = [];
      const errors: string[] = [];

      for (const file of acceptedFiles) {
        const check = validateFile(file);
        if (check.valid) {
          validFiles.push(file);
        } else {
          errors.push(`${file.name}: ${check.error}`);
        }
      }

      if (errors.length > 0) {
        onError(errors.join(" | "));
      }

      if (validFiles.length > 0) {
        onFilesSelected(validFiles);
      }
    },
    [onFilesSelected, onError]
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    disabled: isProcessing,
    multiple: true,
  });

  return (
    <div
      {...getRootProps()}
      className={`relative group cursor-pointer rounded-2xl border-2 border-dashed p-8 sm:p-12 text-center transition-all duration-300 ${
        isDragActive
          ? "border-indigo-500 bg-indigo-50/50 dark:bg-indigo-950/20 scale-[1.01]"
          : isDragReject
          ? "border-red-500 bg-red-50/50 dark:bg-red-950/20"
          : "border-slate-300 dark:border-slate-700/80 bg-white/60 dark:bg-slate-900/40 hover:border-indigo-400 dark:hover:border-indigo-500/80 hover:bg-slate-50/70 dark:hover:bg-slate-800/40"
      }`}
    >
      <input {...getInputProps()} />

      {/* Upload icon circle */}
      <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-tr from-indigo-500/10 via-violet-500/10 to-purple-500/10 dark:from-indigo-500/20 dark:via-violet-500/20 dark:to-purple-500/20 flex items-center justify-center text-indigo-600 dark:text-indigo-400 group-hover:scale-110 transition-transform duration-300">
        <svg
          className="w-8 h-8"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.8}
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>
      </div>

      <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-1">
        {isDragActive
          ? "Drop files here to convert"
          : "Drag & drop files here, or click to browse"}
      </h3>

      <p className="text-sm text-slate-500 dark:text-slate-400 mb-4 max-w-md mx-auto">
        Supports PDF, Word (.docx), Plain Text, HTML, CSV, JSON, and Markdown cleanup.
      </p>

      <div className="inline-flex items-center space-x-2 text-xs font-medium text-slate-400 dark:text-slate-500 bg-slate-100 dark:bg-slate-800/60 px-3 py-1.5 rounded-full">
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <span>Max file size: 50 MB • Batch conversion enabled</span>
      </div>
    </div>
  );
};
