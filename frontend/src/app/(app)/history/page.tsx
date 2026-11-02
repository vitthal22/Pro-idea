"use client";

import { Flame, History } from "lucide-react";

import { AnalysisCard } from "@/components/analysis/AnalysisCard";
import { PageHeader } from "@/components/layout/page-header";
import { ResumeRow } from "@/components/resumes/resume-row";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAnalyses } from "@/hooks/queries/use-analyses";
import { useResumes } from "@/hooks/queries/use-resumes";

export default function HistoryPage() {
  const roasts = useAnalyses();
  const resumes = useResumes();
  const loading = roasts.isPending || resumes.isPending;
  const error = roasts.isError ? roasts.error : resumes.isError ? resumes.error : null;

  return (
    <div>
      <PageHeader
        title="History"
        description="Every roast you have run, and every resume you have uploaded."
      />

      {loading && (
        <div className="space-y-3">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      )}

      {!loading && error && (
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
      )}

      {!loading && !error && (
        <Tabs defaultValue="roasts">
          <TabsList>
            <TabsTrigger value="roasts">
              Roasts{roasts.data ? ` (${roasts.data.total})` : ""}
            </TabsTrigger>
            <TabsTrigger value="resumes">
              Resumes{resumes.data ? ` (${resumes.data.total})` : ""}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="roasts" className="mt-4">
            {roasts.data && roasts.data.total === 0 ? (
              <EmptyState
                icon={Flame}
                title="No roasts yet"
                description="Upload a resume and let four experts tear into it."
                actionLabel="Get roasted"
                actionHref="/upload"
              />
            ) : (
              <div className="grid gap-3">
                {roasts.data?.items.map((roast) => (
                  <AnalysisCard key={roast.id} analysis={roast} />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="resumes" className="mt-4">
            {resumes.data && resumes.data.total === 0 ? (
              <EmptyState
                icon={History}
                title="No resumes yet"
                description="Your uploaded resumes appear here."
                actionLabel="Upload a resume"
                actionHref="/upload"
              />
            ) : (
              <div className="grid gap-3">
                {resumes.data?.items.map((resume) => (
                  <ResumeRow key={resume.id} resume={resume} />
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
