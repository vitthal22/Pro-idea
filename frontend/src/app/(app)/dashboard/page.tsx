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
import { isRunningStatus, type AnalysisListItem } from "@/types/analysis";

const stagger: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.07 } },
};
const fadeUp: Variants = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" } },
};

const MODE_LABELS: Record<AnalysisListItem["analysis_type"], string> = {
  general: "General",
  role_based: "Role-based",
  jd_based: "JD-based",
  custom: "Custom",
};

function LatestRoastCard({ roast }: { roast: AnalysisListItem }) {
  return (
    <div className="flex h-full flex-col justify-between gap-4 rounded-2xl border border-primary/25 bg-gradient-to-br from-primary/10 via-transparent to-transparent p-6 sm:flex-row sm:items-center">
      <div className="flex items-center gap-5">
        {roast.overall_score !== null ? (
          <ScoreRing score={roast.overall_score} size={84} />
        ) : (
          <span className="size-20 rounded-full border-2 border-dashed border-border" aria-hidden />
        )}
        <div>
          <p className="text-sm text-muted-foreground">Latest roast</p>
          <p className="mt-0.5 font-semibold">
            {MODE_LABELS[roast.analysis_type]} analysis
          </p>
          <span className="mt-2 inline-block">
            <StatusBadge status={roast.status} />
          </span>
        </div>
      </div>
      <Button asChild variant="outline" className="shrink-0">
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
      className="group flex h-full flex-col justify-between gap-4 rounded-2xl border border-primary/30 bg-gradient-to-br from-primary/15 via-primary/5 to-transparent p-6 transition-shadow hover:shadow-[0_0_32px_-8px] hover:shadow-primary/40"
    >
      <span className="flex size-11 items-center justify-center rounded-xl bg-primary/20 text-primary">
        <Flame className="size-5" />
      </span>
      <div>
        <p className="font-semibold">Ready to get roasted?</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Four experts, one brutal score — about two minutes.
        </p>
        <span className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-primary">
          Start now
          <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
        </span>
      </div>
    </Link>
  );
}

export default function DashboardPage() {
  const roasts = useAnalyses();
  const resumes = useResumes();

  if (roasts.isPending || resumes.isPending) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-56" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-2xl" />
          ))}
        </div>
        <div className="grid gap-4 lg:grid-cols-3">
          <Skeleton className="h-40 rounded-2xl lg:col-span-2" />
          <Skeleton className="h-40 rounded-2xl" />
        </div>
      </div>
    );
  }

  if (roasts.isError) {
    return (
      <ErrorState
        title="Could not load your overview"
        description={
          roasts.error instanceof Error
            ? roasts.error.message
            : "An unexpected error occurred."
        }
        onRetry={() => roasts.refetch()}
      />
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
    <div className="space-y-4">
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

      <motion.div variants={stagger} initial="hidden" animate="show" className="space-y-4">
        <motion.div variants={fadeUp} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatTile
            icon={<Flame className="size-4 text-primary" />}
            label="Roasts"
            value={String(roastTotal)}
          />
          <StatTile
            icon={<Target className="size-4 text-primary" />}
            label="Average score"
            value={avg !== null ? String(avg) : "—"}
            hint={`${scores.length} scored`}
          />
          <StatTile
            icon={<Trophy className="size-4 text-primary" />}
            label="Best score"
            value={best !== null ? String(best) : "—"}
          />
          <StatTile
            icon={<Upload className="size-4 text-primary" />}
            label="Resumes"
            value={String(resumeTotal)}
          />
        </motion.div>

        <motion.div variants={fadeUp} className="grid gap-4 lg:grid-cols-3">
          {latest ? (
            <div className="lg:col-span-2">
              <LatestRoastCard roast={latest} />
            </div>
          ) : (
            <div className="lg:col-span-2">
              <div className="flex h-full items-center gap-4 rounded-2xl border border-dashed border-border p-6 text-muted-foreground">
                <History className="size-8 shrink-0" />
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
            <h2 className="mb-3 flex items-center gap-2 font-semibold">
              <Sparkles className="size-4 text-primary" aria-hidden />
              Recent roasts
              <Link
                href="/history"
                className="ml-auto text-sm font-normal text-muted-foreground hover:text-foreground"
              >
                View all
              </Link>
            </h2>
            <div className="grid gap-3">
              {roastItems.slice(0, 4).map((roast) => (
                <AnalysisCard key={roast.id} analysis={roast} />
              ))}
            </div>
          </motion.div>
        )}

        {resumeTotal > 0 && (
          <motion.div variants={fadeUp}>
            <h2 className="mb-3 font-semibold">Your resumes</h2>
            <div className="grid gap-3">
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
