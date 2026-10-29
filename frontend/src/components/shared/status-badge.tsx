"use client";

import { Badge } from "@/components/ui/badge";
import { isRunningStatus, type AnalysisStatus } from "@/types/analysis";

/** Human labels — raw pipeline statuses ("partial", "evaluating") are jargon. */
const STATUS_LABELS: Record<AnalysisStatus, string> = {
  queued: "In progress",
  extracting: "In progress",
  parsing: "In progress",
  evaluating: "In progress",
  scoring: "In progress",
  composing: "In progress",
  completed: "Ready",
  partial: "Incomplete",
  failed: "Failed",
};

/** One status badge everywhere lists show an analysis state. */
export function StatusBadge({ status }: { status: AnalysisStatus }) {
  if (isRunningStatus(status)) {
    return (
      <Badge
        variant="outline"
        className="gap-1.5 border-primary/40 bg-primary/10 text-primary"
      >
        <span
          className="size-1.5 animate-pulse rounded-full bg-primary"
          aria-hidden
        />
        {STATUS_LABELS[status]}
      </Badge>
    );
  }
  if (status === "partial") {
    return (
      <Badge
        variant="outline"
        className="border-yellow-500/40 bg-yellow-500/10 text-yellow-600 dark:text-yellow-500"
        title="The roast hit an error and came back incomplete — open it to try again."
      >
        {STATUS_LABELS[status]}
      </Badge>
    );
  }
  if (status === "failed") {
    return <Badge variant="destructive">{STATUS_LABELS[status]}</Badge>;
  }
  return <Badge variant="default">{STATUS_LABELS[status]}</Badge>;
}
