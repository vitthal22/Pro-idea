"use client";

import { FileUp, RefreshCw } from "lucide-react";
import Link from "next/link";

import { AnalysisCard } from "@/components/analysis/AnalysisCard";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAnalyses } from "@/hooks/queries/use-analyses";

export default function DashboardPage() {
  const { data, isPending, isError, refetch, error } = useAnalyses();

  if (isPending) {
    return (
      <div className="grid gap-3">
        <Skeleton className="h-28 w-full" />
        <Skeleton className="h-28 w-full" />
        <Skeleton className="h-28 w-full" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="mx-auto max-w-md rounded-lg border p-8 text-center">
        <p className="font-medium">Could not load analyses</p>
        <p className="text-muted-foreground mt-1 text-sm">
          {error instanceof Error
            ? error.message
            : "An unexpected error occurred."}
        </p>
        <Button variant="outline" className="mt-4" onClick={() => refetch()}>
          <RefreshCw className="size-4" />
          Retry
        </Button>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="mx-auto max-w-md rounded-lg border p-8 text-center">
        <p className="font-medium">No analyses yet</p>
        <p className="text-muted-foreground mt-1 text-sm">
          Upload a resume and get your first brutally honest roast.
        </p>
        <Button className="mt-4" asChild>
          <Link href="/upload">
            <FileUp className="size-4" />
            Upload a resume
          </Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="grid gap-3">
      {data.map((analysis) => (
        <AnalysisCard key={analysis.id} analysis={analysis} />
      ))}
    </div>
  );
}
