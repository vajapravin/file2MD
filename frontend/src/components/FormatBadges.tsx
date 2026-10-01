import React from "react";

const FORMATS = [
  { ext: "PDF", desc: "Documents & Tables", color: "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20" },
  { ext: "DOCX", desc: "Word Files", color: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20" },
  { ext: "HTML", desc: "Webpages", color: "bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/20" },
  { ext: "CSV", desc: "Data Tables", color: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20" },
  { ext: "JSON", desc: "Structured Data", color: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20" },
  { ext: "TXT", desc: "Plain Text", color: "bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border-cyan-500/20" },
  { ext: "MD", desc: "Cleanup & Norm", color: "bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20" },
];

export const FormatBadges: React.FC = () => {
  return (
    <div className="flex flex-wrap items-center justify-center gap-2 py-4">
      <span className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider mr-1">
        Supported formats:
      </span>
      {FORMATS.map((fmt) => (
        <div
          key={fmt.ext}
          className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border ${fmt.color}`}
        >
          <span className="font-bold">{fmt.ext}</span>
          <span className="opacity-70 hidden sm:inline">• {fmt.desc}</span>
        </div>
      ))}
    </div>
  );
};
