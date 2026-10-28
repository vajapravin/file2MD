import React, { useState } from "react";

interface UrlConvertInputProps {
  onUrlSubmit: (url: string) => Promise<void>;
  isProcessing: boolean;
  onError: (msg: string) => void;
}

export const UrlConvertInput: React.FC<UrlConvertInputProps> = ({
  onUrlSubmit,
  isProcessing,
  onError,
}) => {
  const [url, setUrl] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanUrl = url.trim();
    if (!cleanUrl) {
      onError("Please enter a valid website URL.");
      return;
    }

    if (!/^https?:\/\//i.test(cleanUrl)) {
      onError("URL must start with http:// or https://");
      return;
    }

    try {
      await onUrlSubmit(cleanUrl);
      setUrl("");
    } catch {
      // Error handling is handled in parent callback
    }
  };

  const handleExampleClick = (exampleUrl: string) => {
    setUrl(exampleUrl);
  };

  return (
    <div className="rounded-2xl border-2 border-slate-300 dark:border-slate-700/80 bg-white/60 dark:bg-slate-900/40 p-6 sm:p-8 text-left transition-all duration-300 shadow-sm">
      <div className="flex items-center space-x-3 mb-4">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-indigo-500/10 via-violet-500/10 to-purple-500/10 dark:from-indigo-500/20 dark:via-violet-500/20 dark:to-purple-500/20 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.8}
              d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
            />
          </svg>
        </div>
        <div>
          <h3 className="text-base font-semibold text-slate-800 dark:text-slate-100">
            Convert Web Page URL
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Fetch any article, documentation, or public webpage into clean
            Markdown
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative flex items-center">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 dark:text-slate-500">
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"
              />
            </svg>
          </div>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://en.wikipedia.org/wiki/Markdown"
            disabled={isProcessing}
            className="w-full pl-10 pr-20 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800/80 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 transition-all"
          />
          {url && !isProcessing && (
            <button
              type="button"
              onClick={() => setUrl("")}
              className="absolute right-2.5 text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 px-1.5 py-0.5 rounded"
            >
              Clear
            </button>
          )}
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-1">
          <div className="flex items-center space-x-1.5 text-xs text-slate-500 dark:text-slate-400">
            <span className="font-medium">Try:</span>
            <button
              type="button"
              onClick={() =>
                handleExampleClick("https://en.wikipedia.org/wiki/Markdown")
              }
              className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline bg-indigo-50 dark:bg-indigo-950/40 px-2 py-0.5 rounded"
            >
              Wikipedia Markdown
            </button>
            <button
              type="button"
              onClick={() => handleExampleClick("https://example.com")}
              className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline bg-indigo-50 dark:bg-indigo-950/40 px-2 py-0.5 rounded"
            >
              Example Domain
            </button>
          </div>

          <button
            type="submit"
            disabled={isProcessing || !url.trim()}
            className="px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:opacity-50 text-white shadow-sm shadow-indigo-600/30 transition-all flex items-center justify-center space-x-2"
          >
            {isProcessing ? (
              <>
                <svg
                  className="w-4 h-4 animate-spin"
                  viewBox="0 0 24 24"
                  fill="none"
                >
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
                <span>Fetching & Converting...</span>
              </>
            ) : (
              <>
                <span>Convert URL</span>
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
                    d="M14 5l7 7m0 0l-7 7m7-7H3"
                  />
                </svg>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
