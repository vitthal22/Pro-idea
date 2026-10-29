"use client";

import { FileText } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { formatDate } from "@/lib/format";
import type { ResumeResponse } from "@/types/resume";

// Backend parsing_status values: pending (while extracting), completed, failed.
const PARSING_STATUS: Record<
  string,
  { label: string; variant: "default" | "secondary" | "destructive" }
> = {
  completed: { label: "Parsed", variant: "default" },
  pending: { label: "Processing", variant: "secondary" },
  failed: { label: "Failed", variant: "destructive" },
};

function formatSize(bytes: number): string {
  return `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

/** One uploaded resume as a card row (no detail page exists yet). */
export function ResumeRow({ resume }: { resume: ResumeResponse }) {
  const status = PARSING_STATUS[resume.parsing_status] ?? {
    label: resume.parsing_status,
    variant: "secondary" as const,
  };

  return (
    // No resume detail page exists yet — the row is a card, not a link.
    <div className="flex items-center gap-4 rounded-xl border border-border bg-card p-4">
      <FileText className="size-5 shrink-0 text-muted-foreground" />
      <div className="min-w-0 flex-1">
        <p className="truncate font-medium">{resume.original_name}</p>
        <p className="text-xs text-muted-foreground">
          {formatSize(resume.file_size)} • {formatDate(resume.created_at)}
        </p>
      </div>
      <Badge variant={status.variant}>{status.label}</Badge>
    </div>
  );
}
