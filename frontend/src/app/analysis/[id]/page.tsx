"use client";

import { use, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { FileUp } from "lucide-react";

import { RoastResult } from "@/components/analysis/RoastResult";
import { StageProgress } from "@/components/analysis/StageProgress";
import { ErrorState } from "@/components/shared/ErrorState";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useStartAnalysis } from "@/hooks/mutations/use-start-analysis";
import { useAnalysis } from "@/hooks/queries/use-analyses";
import { Sidebar } from "@/components/layout/Sidebar";
import { isRunningStatus } from "@/types/analysis";

export default function AnalysisPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const { data, isPending, isError, error, refetch } = useAnalysis(id);
  const startAnalysis = useStartAnalysis();
  const [startError, setStartError] = useState<string | null>(null);

  function handleRetry() {
    if (!data) return;
    setStartError(null);
    startAnalysis.mutate(
      { resumeId: data.resume_id },
      {
        onSuccess: (created) =>
          router.push(`/analysis/${created.analysis_id}`),
        onError: (err) =>
          setStartError(
            err instanceof Error ? err.message : "Could not start a new roast.",
          ),
      },
    );
  }

  if (isPending) {
    return (
      <div className="min-h-screen bg-background">
        <Sidebar />
        <div className="mx-auto max-w-2xl space-y-4 py-10">
          <Skeleton className="h-28 w-full rounded-2xl" />
          <Skeleton className="h-40 w-full rounded-2xl" />
          <Skeleton className="h-40 w-full rounded-2xl" />
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="min-h-screen bg-background">
        <Sidebar />
        <div className="p-6">
          <ErrorState
            title="Could not load this analysis"
            description={
              error instanceof Error
                ? error.message
                : "An unexpected error occurred."
            }
            onRetry={() => refetch()}
          />
        </div>
      </div>
    );
  }

  const running = isRunningStatus(data.status);

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />

      <div className="mx-auto max-w-2xl py-10">
        {running && <StageProgress status={data.status} />}

        {!running && data.status === "failed" && (
          <div className="mx-auto max-w-md rounded-2xl border border-border bg-card p-8 text-center">
            <h2 className="text-xl font-semibold">The roast burned</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              {data.error_message ?? "The pipeline failed unexpectedly."}
            </p>
            {startError && (
              <p className="mt-2 text-sm text-destructive">{startError}</p>
            )}
            <Button onClick={handleRetry} className="mt-6">
              Try roasting again
            </Button>
          </div>
        )}

        {!running && data.status !== "failed" && data.result && (
          <>
            <div className="mb-5 flex items-center justify-between">
              <h1 className="text-2xl font-bold">Your roast</h1>
              <Button asChild variant="outline">
                <Link href="/upload">
                  <FileUp className="size-4" />
                  Roast another
                </Link>
              </Button>
            </div>
            <RoastResult status={data.status} result={data.result} />
          </>
        )}
      </div>
    </div>
  );
}
