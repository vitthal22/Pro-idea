"use client";

import { use, useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { FileUp } from "lucide-react";

import { RoastResult } from "@/components/analysis/RoastResult";
import { StageProgress } from "@/components/analysis/StageProgress";
import { ErrorState } from "@/components/shared/ErrorState";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/layout/page-header";
import { useStartAnalysis } from "@/hooks/mutations/use-start-analysis";
import { useAnalysisStream } from "@/hooks/use-analysis-stream";
import { useAnalysis } from "@/hooks/queries/use-analyses";
import { isRunningStatus } from "@/types/analysis";

export default function AnalysisPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  // The SSE stream drives live updates; polling is the fallback (off while
  // the stream is connected so we don't double-hit the API).
  const [streamActive, setStreamActive] = useState(true);
  const analysis = useAnalysis(id, { poll: !streamActive });
  const { data, isPending, isError, error, refetch } = analysis;
  const startAnalysis = useStartAnalysis();
  const [startError, setStartError] = useState<string | null>(null);

  const running = data ? isRunningStatus(data.status) : false;

  const onStreamEvent = useCallback(
    (event: { kind: string }) => {
      // Every stream event means server state moved — refetch the detail.
      void refetch();
      if (event.kind !== "status") {
        // Terminal: stop trusting the stream; the detail query settles it.
        setStreamActive(false);
      }
    },
    [refetch],
  );
  const onStreamError = useCallback(() => setStreamActive(false), []);

  useAnalysisStream({
    id,
    enabled: running && streamActive,
    onEvent: onStreamEvent,
    onError: onStreamError,
  });

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
      <div className="mx-auto max-w-2xl space-y-4 py-4">
        <Skeleton className="h-28 w-full rounded-2xl" />
        <Skeleton className="h-40 w-full rounded-2xl" />
        <Skeleton className="h-40 w-full rounded-2xl" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <ErrorState
        title="Could not load this analysis"
        description={
          error instanceof Error
            ? error.message
            : "An unexpected error occurred."
        }
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <div className="mx-auto max-w-2xl">
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
          <PageHeader
            title="Your roast"
            actions={
              <Button asChild variant="outline">
                <Link href="/upload">
                  <FileUp className="size-4" />
                  Roast another
                </Link>
              </Button>
            }
          />
          <RoastResult status={data.status} result={data.result} />
        </>
      )}
    </div>
  );
}
