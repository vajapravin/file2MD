import React from "react";
import { UploadedFileItem } from "../types";
import { formatFileSize } from "../utils/fileValidation";

interface FileListProps {
  files: UploadedFileItem[];
  selectedId: string | null;
  onSelectFile: (id: string) => void;
  onRemoveFile: (id: string) => void;
  onConvertAll: () => void;
  onClearAll: () => void;
  isConverting: boolean;
}

export const FileList: React.FC<FileListProps> = ({
  files,
  selectedId,
  onSelectFile,
  onRemoveFile,
  onConvertAll,
  onClearAll,
  isConverting,
}) => {
  if (files.length === 0) return null;

  const hasPending = files.some((f) => f.status === "idle");

  return (
    <div className="bg-white/70 dark:bg-slate-900/50 backdrop-blur-md rounded-2xl border border-slate-200 dark:border-slate-800 p-4 sm:p-5 shadow-sm">
      <div className="flex items-center justify-between mb-3 pb-3 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center space-x-2">
          <span className="font-semibold text-sm text-slate-800 dark:text-slate-200">
            Files Queue ({files.length})
          </span>
          {files.filter((f) => f.status === "success").length > 0 && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400 font-medium">
              {files.filter((f) => f.status === "success").length} ready
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {hasPending && (
            <button
              onClick={onConvertAll}
              disabled={isConverting}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white shadow-sm shadow-indigo-600/30 transition-colors flex items-center space-x-1.5"
            >
              {isConverting ? (
                <>
                  <svg className="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  <span>Converting...</span>
                </>
              ) : (
                <>
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <span>Convert All</span>
                </>
              )}
            </button>
          )}

          <button
            onClick={onClearAll}
            disabled={isConverting}
            className="px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            Clear
          </button>
        </div>
      </div>

      {/* List items */}
      <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
        {files.map((item) => {
          const isSelected = item.id === selectedId;

          return (
            <div
              key={item.id}
              onClick={() => onSelectFile(item.id)}
              className={`group flex items-center justify-between p-3 rounded-xl border text-left cursor-pointer transition-all duration-200 ${
                isSelected
                  ? "bg-indigo-50/80 dark:bg-indigo-950/40 border-indigo-300 dark:border-indigo-700/80 shadow-sm"
                  : "bg-slate-50/50 dark:bg-slate-800/30 border-slate-200/80 dark:border-slate-800 hover:bg-slate-100/70 dark:hover:bg-slate-800/60"
              }`}
            >
              <div className="flex items-center space-x-3 min-w-0 pr-2">
                <span className="px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider bg-slate-200/80 dark:bg-slate-700 text-slate-700 dark:text-slate-300">
                  {item.format.replace(".", "") || "FILE"}
                </span>

                <div className="min-w-0">
                  <p className="text-xs font-medium text-slate-800 dark:text-slate-200 truncate">
                    {item.name}
                  </p>
                  <p className="text-[11px] text-slate-400 dark:text-slate-500">
                    {formatFileSize(item.size)}
                    {item.metadata && (
                      <span className="ml-1 text-slate-500 dark:text-slate-400">
                        • {item.metadata.conversion_time_ms}ms
                      </span>
                    )}
                  </p>
                </div>
              </div>

              {/* Status and Actions */}
              <div className="flex items-center space-x-2 shrink-0">
                {item.status === "uploading" && (
                  <span className="flex items-center text-xs text-indigo-600 dark:text-indigo-400">
                    <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                  </span>
                )}

                {item.status === "success" && (
                  <span className="flex items-center space-x-1 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                    <span className="hidden sm:inline">Ready</span>
                  </span>
                )}

                {item.status === "error" && (
                  <span className="flex items-center space-x-1 text-xs text-red-500 font-medium">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    <span className="hidden sm:inline">Failed</span>
                  </span>
                )}

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onRemoveFile(item.id);
                  }}
                  className="p-1 rounded-md text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
                  aria-label="Remove file"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
