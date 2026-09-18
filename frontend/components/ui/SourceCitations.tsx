import { ExternalLink, BookOpen } from "lucide-react";
import type { RetrievedSource } from "@/lib/types";

const SOURCE_LABELS: Record<RetrievedSource["source_type"], string> = {
  rbi_advisory: "RBI Advisory",
  npci_advisory: "NPCI Advisory",
  cybercrime_faq: "Cybercrime Portal FAQ",
  scam_pattern: "Known Scam Pattern",
};

interface SourceCitationsProps {
  sources: RetrievedSource[];
}

export default function SourceCitations({ sources }: SourceCitationsProps) {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-3 pt-3 border-t border-slate-700/50">
      <p className="text-xs text-slate-500 mb-2 flex items-center gap-1">
        <BookOpen className="w-3.5 h-3.5" />
        Sources
      </p>
      <div className="flex flex-col gap-1.5">
        {sources.map((source) => (
          <div key={source.id} className="flex items-start gap-2 text-xs">
            <span className="mt-0.5 flex-shrink-0 px-1.5 py-0.5 rounded bg-slate-700 text-slate-400">
              {SOURCE_LABELS[source.source_type]}
            </span>
            <div className="flex flex-col gap-0.5 min-w-0">
              <span className="text-slate-300 font-medium truncate">{source.title}</span>
              <span className="text-slate-500 line-clamp-2">{source.snippet}</span>
            </div>
            {source.source_url && (
              <a
                href={source.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-shrink-0 text-brand-400 hover:text-brand-300"
                aria-label={`Open source: ${source.title}`}
              >
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
