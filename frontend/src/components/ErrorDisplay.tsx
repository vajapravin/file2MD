import React from "react";

interface ErrorDisplayProps {
  message: string | null;
  onDismiss: () => void;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  message,
  onDismiss,
}) => {
  if (!message) return null;

  return (
    <div className="flex items-center justify-between p-4 mb-4 rounded-xl border border-red-200 dark:border-red-900/60 bg-red-50/90 dark:bg-red-950/40 text-red-700 dark:text-red-300 shadow-sm animate-fadeIn">
      <div className="flex items-center space-x-3">
        <svg
          className="w-5 h-5 shrink-0 text-red-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <span className="text-xs sm:text-sm font-medium">{message}</span>
      </div>

      <button
        onClick={onDismiss}
        className="p-1 rounded-lg text-red-400 hover:text-red-600 dark:hover:text-red-200 hover:bg-red-100 dark:hover:bg-red-900/50 transition-colors"
        aria-label="Dismiss error"
      >
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
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>
  );
};
