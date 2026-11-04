"use client";

import { useRouter } from "next/navigation";
import { use, useEffect } from "react";

import { RoastReport } from "@/components/analysis/RoastResult";
import { ErrorState } from "@/components/shared/ErrorState";
import { Skeleton } from "@/components/ui/skeleton";
import { useAnalysis } from "@/hooks/queries/use-analyses";

/**
 * The full roast report. Deliberately behind its own route: the verdict screen
 * is the product, this page is the document you work through (and print).
 * Anything that is not `completed` bounces back to the verdict.
 */
export default function ReportPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const { data, isPending, isError, error, refetch } = useAnalysis(id, {
    poll: false,
  });

  useEffect(() => {
    if (data && data.status !== "completed") {
      router.replace(`/analysis/${id}`);
    }
  }, [data, id, router]);

  if (isPending) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-24 w-full rounded-xl" />
        <Skeleton className="h-40 w-full rounded-xl" />
        <Skeleton className="h-40 w-full rounded-xl" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <ErrorState
        title="Could not load this report"
        description={
          error instanceof Error ? error.message : "An unexpected error occurred."
        }
        onRetry={() => refetch()}
      />
    );
  }

  if (data.status !== "completed" || !data.result) {
    return (
      <div className="mx-auto max-w-md rounded-xl border border-border bg-card p-6 text-center">
        <p className="text-sm text-muted-foreground">
          This roast is not finished yet — taking you back to the verdict…
        </p>
      </div>
    );
  }

  return (
    <RoastReport
      result={data.result}
      verdict={data.score_verdict}
      analysisType={data.analysis_type}
      analysisId={id}
    />
  );
}
