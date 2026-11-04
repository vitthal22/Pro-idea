"use client";

import { useState } from "react";
import { Flame, History } from "lucide-react";

import { AnalysisCard } from "@/components/analysis/AnalysisCard";
import { PageHeader } from "@/components/layout/page-header";
import { ResumeRow } from "@/components/resumes/resume-row";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAnalyses } from "@/hooks/queries/use-analyses";
import { useResumes } from "@/hooks/queries/use-resumes";

const PAGE_SIZE = 10;

/** Compact rows in a shared divided container (no per-row cards). */
const LIST_CLASS =
  "divide-y divide-border overflow-hidden rounded-xl border border-border bg-card";

export default function HistoryPage() {
  const [visible, setVisible] = useState(PAGE_SIZE);
  const roasts = useAnalyses({ limit: visible });
  const resumes = useResumes();
  const loading = roasts.isPending || resumes.isPending;
  const error = roasts.isError ? roasts.error : resumes.isError ? resumes.error : null;

  const header = (
    <PageHeader
      title="History"
      description="Every roast you have run, and every resume you have uploaded."
    />
  );

  if (loading) {
    return (
      <div className="space-y-6">
        {header}
        <div className="space-y-2">
          <Skeleton className="h-10 w-48" />
          <Skeleton className="h-64 w-full rounded-xl" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        {header}
        <ErrorState
          title="Could not load your history"
          description={
            error instanceof Error ? error.message : "An unexpected error occurred."
          }
          onRetry={() => {
            roasts.refetch();
            resumes.refetch();
          }}
        />
      </div>
    );
  }

  const roastTotal = roasts.data?.total ?? 0;
  const shown = roasts.data?.items.length ?? 0;

  return (
    <div>
      {header}

      <Tabs defaultValue="roasts" className="gap-3">
        <TabsList>
          <TabsTrigger value="roasts">
            Roasts{roasts.data ? ` (${roasts.data.total})` : ""}
          </TabsTrigger>
          <TabsTrigger value="resumes">
            Resumes{resumes.data ? ` (${resumes.data.total})` : ""}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="roasts">
          {roastTotal === 0 ? (
            <EmptyState
              icon={Flame}
              title="No roasts yet"
              description="Upload a resume and let four experts tear into it."
              actionLabel="Get roasted"
              actionHref="/upload"
            />
          ) : (
            <div className="space-y-3">
              <div className={LIST_CLASS}>
                {roasts.data?.items.map((roast) => (
                  <AnalysisCard key={roast.id} analysis={roast} />
                ))}
              </div>
              {shown < roastTotal && (
                <div className="flex justify-center">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setVisible((current) => current + PAGE_SIZE)}
                  >
                    Load {Math.min(PAGE_SIZE, roastTotal - shown)} more
                  </Button>
                </div>
              )}
            </div>
          )}
        </TabsContent>

        <TabsContent value="resumes">
          {resumes.data && resumes.data.total === 0 ? (
            <EmptyState
              icon={History}
              title="No resumes yet"
              description="Your uploaded resumes appear here."
              actionLabel="Upload a resume"
              actionHref="/upload"
            />
          ) : (
            <div className={LIST_CLASS}>
              {resumes.data?.items.map((resume) => (
                <ResumeRow key={resume.id} resume={resume} />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
