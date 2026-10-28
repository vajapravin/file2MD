import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import { UploadedFileItem } from "../types";
import { copyToClipboard, downloadMarkdown } from "../utils/download";

interface MarkdownPreviewProps {
  item: UploadedFileItem | null;
}

export const MarkdownPreview: React.FC<MarkdownPreviewProps> = ({ item }) => {
  const [viewMode, setViewMode] = useState<"rendered" | "raw">("rendered");
  const [copied, setCopied] = useState(false);

  if (!item) {
    return (
      <div className="h-full min-h-[460px] flex flex-col items-center justify-center p-8 text-center rounded-2xl border border-dashed border-slate-200 dark:border-slate-800 bg-white/40 dark:bg-slate-900/20 backdrop-blur-sm">
        <div className="w-14 h-14 mb-3 rounded-2xl bg-slate-100 dark:bg-slate-800/80 flex items-center justify-center text-slate-400">
          <svg
            className="w-7 h-7"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        </div>
        <h4 className="text-base font-semibold text-slate-700 dark:text-slate-300 mb-1">
          No Document Selected
        </h4>
        <p className="text-xs text-slate-400 dark:text-slate-500 max-w-xs">
          Upload and convert a file to preview generated Markdown with full
          structure preservation.
        </p>
      </div>
    );
  }

  if (item.status === "uploading") {
    return (
      <div className="h-full min-h-[460px] flex flex-col items-center justify-center p-8 text-center rounded-2xl border border-slate-200 dark:border-slate-800 bg-white/60 dark:bg-slate-900/40 backdrop-blur-sm">
        <div className="w-12 h-12 mb-4 rounded-xl bg-indigo-50 dark:bg-indigo-950/60 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
          <svg className="w-6 h-6 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v8H4z"
            />
          </svg>
        </div>
        <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-1">
          Converting {item.name}...
        </h4>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Parsing structure, tables, and typography via MarkItDown engine.
        </p>
      </div>
    );
  }

  if (item.status === "error") {
    return (
      <div className="h-full min-h-[460px] flex flex-col items-center justify-center p-8 text-center rounded-2xl border border-red-200 dark:border-red-900/40 bg-red-50/30 dark:bg-red-950/20 backdrop-blur-sm">
        <div className="w-12 h-12 mb-3 rounded-full bg-red-100 dark:bg-red-900/40 flex items-center justify-center text-red-500">
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <h4 className="text-sm font-semibold text-red-700 dark:text-red-400 mb-1">
          Conversion Failed
        </h4>
        <p className="text-xs text-red-600/80 dark:text-red-300 max-w-sm mb-4">
          {item.error || "Unable to extract content from this document."}
        </p>
      </div>
    );
  }

  const markdown = item.markdown || "";
  const wordCount = markdown.trim() ? markdown.trim().split(/\s+/).length : 0;
  const charCount = markdown.length;

  const handleCopy = async () => {
    const success = await copyToClipboard(markdown);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    downloadMarkdown(markdown, item.name);
  };

  return (
    <div className="flex flex-col h-full rounded-2xl border border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/60 backdrop-blur-md shadow-sm overflow-hidden">
      {/* Header bar */}
      <div className="px-5 py-3.5 border-b border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3 bg-slate-50/70 dark:bg-slate-800/40">
        <div className="min-w-0">
          <div className="flex items-center space-x-2">
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 truncate">
              {item.name}
            </h3>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-indigo-100 dark:bg-indigo-950/70 text-indigo-700 dark:text-indigo-300">
              .MD
            </span>
          </div>
          <div className="flex items-center space-x-3 text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">
            <span>{wordCount} words</span>
            <span>•</span>
            <span>{charCount} characters</span>
            {item.metadata && (
              <>
                <span>•</span>
                <span className="text-emerald-600 dark:text-emerald-400 font-medium">
                  Converted in {item.metadata.conversion_time_ms}ms
                </span>
              </>
            )}
          </div>
        </div>

        {/* View Mode & Actions */}
        <div className="flex items-center space-x-2">
          {/* Mode toggle */}
          <div className="flex p-0.5 rounded-lg bg-slate-200/70 dark:bg-slate-800 border border-slate-300/60 dark:border-slate-700/60 text-xs">
            <button
              onClick={() => setViewMode("rendered")}
              className={`px-3 py-1 rounded-md font-medium transition-colors ${
                viewMode === "rendered"
                  ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
              }`}
            >
              Preview
            </button>
            <button
              onClick={() => setViewMode("raw")}
              className={`px-3 py-1 rounded-md font-medium transition-colors ${
                viewMode === "raw"
                  ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
              }`}
            >
              Raw MD
            </button>
          </div>

          {/* Copy button */}
          <button
            onClick={handleCopy}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-colors ${
              copied
                ? "bg-emerald-600 text-white"
                : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700"
            }`}
          >
            {copied ? (
              <>
                <svg
                  className="w-3.5 h-3.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2.5}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                <span>Copied!</span>
              </>
            ) : (
              <>
                <svg
                  className="w-3.5 h-3.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"
                  />
                </svg>
                <span>Copy</span>
              </>
            )}
          </button>

          {/* Download button */}
          <button
            onClick={handleDownload}
            className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm shadow-indigo-600/30 transition-colors flex items-center space-x-1.5"
          >
            <svg
              className="w-3.5 h-3.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
              />
            </svg>
            <span>Download .md</span>
          </button>
        </div>
      </div>

      {/* Content pane */}
      <div className="flex-1 p-6 overflow-y-auto max-h-[600px]">
        {viewMode === "rendered" ? (
          <div className="prose dark:prose-invert max-w-none text-slate-800 dark:text-slate-200">
            <ReactMarkdown>{markdown}</ReactMarkdown>
          </div>
        ) : (
          <pre className="font-mono text-xs text-slate-800 dark:text-slate-200 whitespace-pre-wrap break-words leading-relaxed select-all bg-slate-50 dark:bg-slate-950 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
            {markdown}
          </pre>
        )}
      </div>
    </div>
  );
};
