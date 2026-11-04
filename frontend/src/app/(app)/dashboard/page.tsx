"use client";

import { motion, type Variants } from "framer-motion";
import { ArrowRight, Flame, History, Sparkles, Target, Trophy, Upload } from "lucide-react";
import Link from "next/link";

import { AnalysisCard } from "@/components/analysis/AnalysisCard";
import { ScoreRing } from "@/components/analysis/score-ring";
import { PageHeader } from "@/components/layout/page-header";
import { ResumeRow } from "@/components/resumes/resume-row";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { StatTile } from "@/components/shared/stat-tile";
import { StatusBadge } from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAnalyses } from "@/hooks/queries/use-analyses";
import { useResumes } from "@/hooks/queries/use-resumes";
import { analysisModeLabel } from "@/lib/analysis-modes";
import { isRunningStatus, type AnalysisListItem } from "@/types/analysis";

const stagger: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.07 } },
};
const fadeUp: Variants = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" } },
};

function LatestRoastCard({ roast }: { roast: AnalysisListItem }) {
  return (
    <div className="flex h-full flex-wrap items-center justify-between gap-4 rounded-xl border border-primary/25 bg-gradient-to-br from-primary/10 via-transparent to-transparent p-4">
      <div className="flex min-w-0 items-center gap-4">
        {roast.overall_score !== null ? (
          <ScoreRing score={roast.overall_score} size={64} />
        ) : (
          <span
            className="size-16 rounded-full border-2 border-dashed border-border"
            aria-hidden
          />
        )}
        <div className="min-w-0">
          <p className="text-xs text-muted-foreground">Latest roast</p>
          <p className="truncate text-sm font-semibold">
            {analysisModeLabel(roast.analysis_type)} analysis
          </p>
          <span className="mt-1.5 inline-block">
            <StatusBadge status={roast.status} />
          </span>
        </div>
      </div>
      <Button asChild variant="outline" size="sm" className="shrink-0">
        <Link href={`/analysis/${roast.id}`}>
          {isRunningStatus(roast.status)
            ? "Watch live"
            : roast.status === "completed"
              ? "View roast"
              : "View status"}
          <ArrowRight className="size-4" />
        </Link>
      </Button>
    </div>
  );
}

function NewRoastTile() {
  return (
    <Link
      href="/upload"
      className="group flex h-full items-center gap-3 rounded-xl border border-primary/30 bg-gradient-to-br from-primary/15 via-primary/5 to-transparent p-4 transition-shadow hover:shadow-[0_0_32px_-8px] hover:shadow-primary/40"
    >
      <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary/20 text-primary">
        <Flame className="size-4" />
      </span>
      <div className="min-w-0">
        <p className="text-sm font-semibold">Ready to get roasted?</p>
        <p className="mt-0.5 truncate text-xs text-muted-foreground">
          Four experts, one brutal score.
        </p>
      </div>
      <ArrowRight className="ml-auto size-4 shrink-0 text-primary transition-transform group-hover:translate-x-0.5" />
    </Link>
  );
}

export default function DashboardPage() {
  const roasts = useAnalyses();
  const resumes = useResumes();

  const header = (
    <PageHeader
      title="Overview"
      description="Your resumes and the roasts they have endured."
      actions={
        <Button asChild>
          <Link href="/upload">
            <Upload className="size-4" />
            New roast
          </Link>
        </Button>
      }
    />
  );

  if (roasts.isPending || resumes.isPending) {
    return (
      <div className="space-y-6">
        {header}
        <div className="grid auto-rows-fr grid-cols-2 gap-2 sm:gap-3 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-16 rounded-xl" />
          ))}
        </div>
        <div className="grid gap-3 lg:grid-cols-3">
          <Skeleton className="h-24 rounded-xl lg:col-span-2" />
          <Skeleton className="h-24 rounded-xl" />
        </div>
      </div>
    );
  }

  if (roasts.isError) {
    return (
      <div className="space-y-6">
        {header}
        <ErrorState
          title="Could not load your overview"
          description={
            roasts.error instanceof Error
              ? roasts.error.message
              : "An unexpected error occurred."
          }
          onRetry={() => roasts.refetch()}
        />
      </div>
    );
  }

  const roastItems = roasts.data?.items ?? [];
  const roastTotal = roasts.data?.total ?? 0;
  const scores = roastItems
    .map((item) => item.overall_score)
    .filter((score): score is number => score !== null);
  const avg =
    scores.length > 0
      ? Math.round(scores.reduce((sum, s) => sum + s, 0) / scores.length)
      : null;
  const best = scores.length > 0 ? Math.round(Math.max(...scores)) : null;
  const latest = roastItems[0];
  const resumeItems = resumes.data?.items.slice(0, 4) ?? [];
  const resumeTotal = resumes.data?.total ?? 0;

  if (roastTotal === 0 && resumeTotal === 0) {
    return (
      <EmptyState
        icon={Flame}
        title="Welcome to the roaster"
        description="Upload your resume and four AI experts will tear it apart — honestly, constructively, and in about two minutes."
        actionLabel="Upload your first resume"
        actionHref="/upload"
      />
    );
  }

  return (
    <div className="space-y-6">
      {header}

      <motion.div
        variants={stagger}
        initial="hidden"
        animate="show"
        className="space-y-4"
      >
        <motion.div
          variants={fadeUp}
          className="grid auto-rows-fr grid-cols-2 gap-2 sm:gap-3 lg:grid-cols-4"
        >
          <StatTile
            icon={<Flame className="size-3.5 text-primary" />}
            label="Roasts"
            value={String(roastTotal)}
          />
          <StatTile
            icon={<Target className="size-3.5 text-primary" />}
            label="Average score"
            value={avg !== null ? String(avg) : "—"}
            hint={`${scores.length} scored`}
          />
          <StatTile
            icon={<Trophy className="size-3.5 text-primary" />}
            label="Best score"
            value={best !== null ? String(best) : "—"}
          />
          <StatTile
            icon={<Upload className="size-3.5 text-primary" />}
            label="Resumes"
            value={String(resumeTotal)}
          />
        </motion.div>

        <motion.div variants={fadeUp} className="grid gap-3 lg:grid-cols-3">
          {latest ? (
            <div className="lg:col-span-2">
              <LatestRoastCard roast={latest} />
            </div>
          ) : (
            <div className="lg:col-span-2">
              <div className="flex h-full items-center gap-3 rounded-xl border border-dashed border-border p-4 text-muted-foreground">
                <History className="size-5 shrink-0" />
                <p className="text-sm">
                  No roasts yet — your resume is uploaded and waiting. Start
                  one from the sidebar or the tile on the right.
                </p>
              </div>
            </div>
          )}
          <NewRoastTile />
        </motion.div>

        {roastTotal > 0 && (
          <motion.div variants={fadeUp}>
            <h2 className="mb-2 flex items-center gap-2 text-sm font-semibold">
              <Sparkles className="size-4 text-primary" aria-hidden />
              Recent roasts
              <Link
                href="/history"
                className="ml-auto text-xs font-normal text-muted-foreground hover:text-foreground"
              >
                View all
              </Link>
            </h2>
            <div className="divide-y divide-border overflow-hidden rounded-xl border border-border bg-card">
              {roastItems.slice(0, 4).map((roast) => (
                <AnalysisCard key={roast.id} analysis={roast} />
              ))}
            </div>
          </motion.div>
        )}

        {resumeTotal > 0 && (
          <motion.div variants={fadeUp}>
            <h2 className="mb-2 text-sm font-semibold">Your resumes</h2>
            <div className="divide-y divide-border overflow-hidden rounded-xl border border-border bg-card">
              {resumeItems.map((resume) => (
                <ResumeRow key={resume.id} resume={resume} />
              ))}
            </div>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}
