import clsx from "clsx";
import { AlertTriangle, ShieldCheck, AlertCircle, Info } from "lucide-react";
import type { RiskLevel, ScamClassification } from "@/lib/types";
import { SCAM_CATEGORY_LABELS } from "@/lib/types";

const RISK_CONFIG: Record<
  RiskLevel,
  { icon: typeof AlertTriangle; bgClass: string; textClass: string; label: string }
> = {
  high: {
    icon: AlertTriangle,
    bgClass: "bg-red-900/40 border-red-700/50",
    textClass: "text-red-400",
    label: "High Risk",
  },
  medium: {
    icon: AlertCircle,
    bgClass: "bg-amber-900/40 border-amber-700/50",
    textClass: "text-amber-400",
    label: "Medium Risk",
  },
  low: {
    icon: Info,
    bgClass: "bg-yellow-900/30 border-yellow-700/40",
    textClass: "text-yellow-400",
    label: "Low Risk",
  },
  safe: {
    icon: ShieldCheck,
    bgClass: "bg-green-900/30 border-green-700/40",
    textClass: "text-green-400",
    label: "Looks Safe",
  },
};

interface ScamBadgeProps {
  classification: ScamClassification;
}

export default function ScamBadge({ classification }: ScamBadgeProps) {
  const config = RISK_CONFIG[classification.risk_level];
  const Icon = config.icon;

  return (
    <div
      className={clsx(
        "flex flex-col gap-2 rounded-xl border p-3 mt-2 text-sm",
        config.bgClass
      )}
    >
      {/* Header row */}
      <div className="flex items-center justify-between gap-3">
        <div className={clsx("flex items-center gap-1.5 font-semibold", config.textClass)}>
          <Icon className="w-4 h-4" />
          {config.label}
        </div>
        <span className="text-slate-400 text-xs">
          {Math.round(classification.confidence * 100)}% confidence
        </span>
      </div>

      {/* Category */}
      <div className="flex items-center gap-2">
        <span className="text-slate-400 text-xs">Type:</span>
        <span className="text-slate-200 text-xs font-medium">
          {SCAM_CATEGORY_LABELS[classification.category]}
        </span>
      </div>

      {/* Indicators */}
      {classification.indicators.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-0.5">
          {classification.indicators.map((indicator) => (
            <span
              key={indicator}
              className="px-2 py-0.5 rounded-md bg-slate-800/60 text-slate-300 text-xs"
            >
              {indicator}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
