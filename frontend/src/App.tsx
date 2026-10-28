import { useEffect, useState } from "react";
import {
  convertSingleFile,
  convertUrl,
  fetchHealth,
} from "./services/convertApi";
import { ErrorDisplay } from "./components/ErrorDisplay";
import { FileList } from "./components/FileList";
import { FileUpload } from "./components/FileUpload";
import { FormatBadges } from "./components/FormatBadges";
import { MarkdownPreview } from "./components/MarkdownPreview";
import { Navbar } from "./components/Navbar";
import { UrlConvertInput } from "./components/UrlConvertInput";
import { UploadedFileItem } from "./types";
import { getFileExtension } from "./utils/fileValidation";

export function App() {
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [inputMode, setInputMode] = useState<"file" | "url">("file");
  const [isHealthy, setIsHealthy] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [files, setFiles] = useState<UploadedFileItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [isConverting, setIsConverting] = useState(false);

  // Sync theme to root DOM
  useEffect(() => {
    const root = document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
  }, [theme]);

  // Check backend health periodically
  useEffect(() => {
    let mounted = true;
    const check = async () => {
      try {
        await fetchHealth();
        if (mounted) setIsHealthy(true);
      } catch {
        if (mounted) setIsHealthy(false);
      }
    };

    check();
    const interval = setInterval(check, 10000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };

  const convertFileItem = async (item: UploadedFileItem) => {
    setFiles((prev) =>
      prev.map((f) =>
        f.id === item.id
          ? {
              ...f,
              status: item.sourceUrl ? "processing" : "uploading",
              progress: item.sourceUrl ? 50 : 0,
              error: undefined,
            }
          : f,
      ),
    );

    try {
      if (item.sourceUrl) {
        const response = await convertUrl(item.sourceUrl);
        setFiles((prev) =>
          prev.map((f) =>
            f.id === item.id
              ? {
                  ...f,
                  name: response.filename,
                  size: response.metadata.size_bytes,
                  status: "success",
                  progress: 100,
                  markdown: response.markdown,
                  metadata: response.metadata,
                }
              : f,
          ),
        );
      } else if (item.file) {
        const response = await convertSingleFile(item.file, (job) => {
          setFiles((prev) =>
            prev.map((f) =>
              f.id === item.id
                ? {
                    ...f,
                    status: "processing",
                    progress: job.progress,
                    totalChunks: job.chunks_total,
                    processedChunks: job.chunks_completed,
                    jobMessage: job.message,
                  }
                : f,
            ),
          );
        });

        setFiles((prev) =>
          prev.map((f) =>
            f.id === item.id
              ? {
                  ...f,
                  status: "success",
                  progress: 100,
                  markdown: response.markdown,
                  metadata: response.metadata,
                }
              : f,
          ),
        );
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Conversion failed.";
      setFiles((prev) =>
        prev.map((f) =>
          f.id === item.id
            ? {
                ...f,
                status: "error",
                error: msg,
              }
            : f,
        ),
      );
    }
  };

  const handleUrlSubmit = async (targetUrl: string) => {
    setErrorMessage(null);
    const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const urlItem: UploadedFileItem = {
      id,
      sourceUrl: targetUrl,
      name: targetUrl,
      size: 0,
      format: "url",
      status: "idle",
      progress: 0,
    };

    setFiles((prev) => [urlItem, ...prev]);
    setSelectedId(id);

    setIsConverting(true);
    await convertFileItem(urlItem);
    setIsConverting(false);
  };

  // Add files and immediately trigger conversion for seamless experience
  const handleFilesSelected = async (newFiles: File[]) => {
    setErrorMessage(null);
    const newItems: UploadedFileItem[] = newFiles.map((file) => ({
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      file,
      name: file.name,
      size: file.size,
      format: getFileExtension(file.name),
      status: "idle",
      progress: 0,
    }));

    setFiles((prev) => [...prev, ...newItems]);

    // Select the first new file if none is selected
    if (!selectedId && newItems.length > 0) {
      setSelectedId(newItems[0]?.id ?? null);
    }

    // Auto-convert newly added files
    setIsConverting(true);
    for (const item of newItems) {
      await convertFileItem(item);
    }
    setIsConverting(false);
  };

  const handleConvertAll = async () => {
    const idleFiles = files.filter(
      (f) => f.status === "idle" || f.status === "error",
    );
    if (idleFiles.length === 0) return;

    setIsConverting(true);
    for (const item of idleFiles) {
      await convertFileItem(item);
    }
    setIsConverting(false);
  };

  const handleRemoveFile = (id: string) => {
    setFiles((prev) => {
      const updated = prev.filter((f) => f.id !== id);
      if (selectedId === id) {
        setSelectedId(updated.length > 0 ? (updated[0]?.id ?? null) : null);
      }
      return updated;
    });
  };

  const handleClearAll = () => {
    setFiles([]);
    setSelectedId(null);
    setErrorMessage(null);
  };

  const selectedItem = files.find((f) => f.id === selectedId) || null;

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors duration-200">
      <Navbar isHealthy={isHealthy} theme={theme} onToggleTheme={toggleTheme} />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-10">
        {/* Hero Banner */}
        <div className="text-center max-w-3xl mx-auto mb-8 sm:mb-10">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-800 dark:from-white dark:via-indigo-200 dark:to-slate-300 bg-clip-text text-transparent">
            Convert Any Document to Clean Markdown
          </h2>
          <p className="mt-3 text-sm sm:text-base text-slate-600 dark:text-slate-400">
            Preserve headers, tables, links, and text structure without external
            cloud tracking. Powered by Microsoft's MarkItDown engine.
          </p>

          <FormatBadges />
        </div>

        {/* Global Error Banner */}
        <ErrorDisplay
          message={errorMessage}
          onDismiss={() => setErrorMessage(null)}
        />

        {/* Two-Column App Workspace */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Upload & Queue */}
          <div className="lg:col-span-5 space-y-6">
            {/* Input Mode Selector */}
            <div className="flex items-center justify-center p-1 rounded-xl bg-slate-200/60 dark:bg-slate-800/60 border border-slate-300/60 dark:border-slate-700/60">
              <button
                type="button"
                onClick={() => setInputMode("file")}
                className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-semibold transition-all flex items-center justify-center space-x-1.5 ${
                  inputMode === "file"
                    ? "bg-white dark:bg-slate-900 text-indigo-600 dark:text-indigo-400 shadow-sm"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
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
                    strokeWidth={1.8}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
                <span>Upload Documents</span>
              </button>
              <button
                type="button"
                onClick={() => setInputMode("url")}
                className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-semibold transition-all flex items-center justify-center space-x-1.5 ${
                  inputMode === "url"
                    ? "bg-white dark:bg-slate-900 text-indigo-600 dark:text-indigo-400 shadow-sm"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
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
                    strokeWidth={1.8}
                    d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                  />
                </svg>
                <span>URL to Markdown</span>
              </button>
            </div>

            {inputMode === "file" ? (
              <FileUpload
                onFilesSelected={handleFilesSelected}
                onError={(msg) => setErrorMessage(msg)}
                isProcessing={isConverting}
              />
            ) : (
              <UrlConvertInput
                onUrlSubmit={handleUrlSubmit}
                onError={(msg) => setErrorMessage(msg)}
                isProcessing={isConverting}
              />
            )}

            <FileList
              files={files}
              selectedId={selectedId}
              onSelectFile={(id) => setSelectedId(id)}
              onRemoveFile={handleRemoveFile}
              onConvertAll={handleConvertAll}
              onClearAll={handleClearAll}
              isConverting={isConverting}
            />
          </div>

          {/* Right Column: Interactive Markdown Preview */}
          <div className="lg:col-span-7 h-[580px] sm:h-[640px]">
            <MarkdownPreview item={selectedItem} />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-800 py-6 text-center text-xs text-slate-500 dark:text-slate-400 bg-white/40 dark:bg-slate-900/40 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>file2MD • Open Source MIT License</span>
          <div className="flex items-center space-x-4">
            <a
              href="https://github.com/microsoft/markitdown"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:underline hover:text-indigo-600 dark:hover:text-indigo-400"
            >
              Powered by MarkItDown
            </a>
            <span>•</span>
            <a
              href="https://file2md.vajapravin.me/"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:underline hover:text-indigo-600 dark:hover:text-indigo-400"
            >
              Live Demo
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
