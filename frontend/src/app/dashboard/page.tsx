"use client";

import { FileText, FileUp } from "lucide-react";
import Link from "next/link";

import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useResumes } from "@/hooks/queries/use-resumes";
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

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function ResumeRow({ resume }: { resume: ResumeResponse }) {
  const status = PARSING_STATUS[resume.parsing_status] ?? {
    label: resume.parsing_status,
    variant: "secondary" as const,
  };

  return (
    // No detail page exists yet — the row is a card, not a link.
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

export default function DashboardPage() {
  const resumes = useResumes();

  if (resumes.isPending) {
    return (
      <div className="mx-auto max-w-3xl space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
      </div>
    );
  }

  if (resumes.isError) {
    return (
      <ErrorState
        title="Could not load your resumes"
        description={
          resumes.error instanceof Error
            ? resumes.error.message
            : "An unexpected error occurred."
        }
        onRetry={() => resumes.refetch()}
      />
    );
  }

  if (!resumes.data || resumes.data.total === 0) {
    return (
      <EmptyState
        icon={FileUp}
        title="No resumes yet"
        description="Upload a resume to get your first brutally honest roast."
        actionLabel="Upload a resume"
        actionHref="/upload"
      />
    );
  }

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Your resumes</h1>
        <Button asChild>
          <Link href="/upload">
            <FileUp className="size-4" />
            Upload
          </Link>
        </Button>
      </div>

      <div className="grid gap-3">
        {resumes.data.items.map((resume) => (
          <ResumeRow key={resume.id} resume={resume} />
        ))}
      </div>
    </div>
  );
}
