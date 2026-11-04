"use client";

import Link from "next/link";

import { ScoreRing } from "@/components/analysis/score-ring";
import { StatusBadge } from "@/components/shared/status-badge";
import { formatDate } from "@/lib/format";
import { analysisModeLabel } from "@/lib/analysis-modes";
import { isRunningStatus, type AnalysisListItem } from "@/types/analysis";

/**
 * One roast as a compact list row. The parent owns the container (border +
 * `divide-y`), so rows never stack their own padding and borders.
 */
export function AnalysisCard({ analysis }: { analysis: AnalysisListItem }) {
  const created = formatDate(analysis.created_at);
  const running = isRunningStatus(analysis.status);

  return (
    <Link
      href={`/analysis/${analysis.id}`}
      className="flex items-center gap-3 px-4 py-2 transition-colors hover:bg-muted/40"
    >
      {analysis.overall_score !== null ? (
        <ScoreRing score={analysis.overall_score} size={40} />
      ) : (
        <span
          className="size-10 shrink-0 rounded-full border-2 border-dashed border-border"
          aria-hidden
        />
      )}
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium">
          {analysisModeLabel(analysis.analysis_type)} analysis
        </span>
        <span className="block truncate text-xs text-muted-foreground">
          {running ? "Roasting now — tap to watch live" : `Created ${created}`}
        </span>
      </span>
      <StatusBadge status={analysis.status} />
    </Link>
  );
}
