"use client";

import { Flame, History, Target, Trophy, Upload } from "lucide-react";
import Link from "next/link";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";

import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { StatTile } from "@/components/shared/stat-tile";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/shared/status-badge";
import { useAnalyses } from "@/hooks/queries/use-analyses";
import { useResumes } from "@/hooks/queries/use-resumes";
import { isRunningStatus, type AnalysisListItem } from "@/types/analysis";

const trendConfig = {
  score: { label: "Score", color: "var(--chart-1)" },
} satisfies ChartConfig;

const distConfig = {
  count: { label: "Roasts", color: "var(--chart-1)" },
} satisfies ChartConfig;

const BUCKETS = [
  { label: "0-39", min: 0, max: 39 },
  { label: "40-59", min: 40, max: 59 },
  { label: "60-74", min: 60, max: 74 },
  { label: "75-89", min: 75, max: 89 },
  { label: "90-100", min: 90, max: 100 },
];

function shortDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

function buildChartData(items: AnalysisListItem[]) {
  // API returns newest first — the trend reads oldest → newest.
  const scored = items
    .filter((item) => item.overall_score !== null)
    .reverse();
  const trend = scored.map((item) => ({
    date: shortDate(item.created_at),
    score: Math.round(item.overall_score as number),
  }));
  const scores = scored.map((item) => item.overall_score as number);
  const distribution = BUCKETS.map((bucket) => ({
    bucket: bucket.label,
    count: scores.filter((s) => s >= bucket.min && s <= bucket.max).length,
  }));
  return { trend, scores, distribution };
}

function ActivityFeed({ items }: { items: AnalysisListItem[] }) {
  const recent = items.slice(0, 6);
  return (
    <ul className="space-y-3">
      {recent.map((item) => {
        const running = isRunningStatus(item.status);
        return (
          <li key={item.id} className="flex items-center gap-3 text-sm">
            {item.overall_score !== null ? (
              <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary/12 text-xs font-bold text-primary">
                {Math.round(item.overall_score)}
              </span>
            ) : (
              <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-muted text-muted-foreground">
                <History className="size-4" />
              </span>
            )}
            <span className="min-w-0 flex-1 truncate">
              {running ? (
                <span>{item.analysis_type.replace("_", " ")} analysis</span>
              ) : (
                <Link
                  href={`/analysis/${item.id}`}
                  className="hover:text-primary hover:underline"
                >
                  {item.analysis_type.replace("_", " ")} analysis
                </Link>
              )}
            </span>
            {item.status !== "completed" && <StatusBadge status={item.status} />}
            <span className="shrink-0 text-xs text-muted-foreground">
              {shortDate(item.created_at)}
            </span>
          </li>
        );
      })}
    </ul>
  );
}

export default function AnalyticsPage() {
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
        <Skeleton className="h-64 rounded-2xl" />
      </div>
    );
  }

  if (roasts.isError) {
    return (
      <ErrorState
        title="Could not load analytics"
        description={
          roasts.error instanceof Error
            ? roasts.error.message
            : "An unexpected error occurred."
        }
        onRetry={() => roasts.refetch()}
      />
    );
  }

  const items = roasts.data?.items ?? [];
  const resumeTotal = resumes.data?.total ?? 0;

  if (roasts.data?.total === 0) {
    return (
      <div>
        <PageHeader
          title="Analytics"
          description="What the experts have said about your resumes so far."
        />
        <EmptyState
          icon={Flame}
          title="No data yet"
          description="Run your first roast and this page fills up with your score history."
          actionLabel="Get roasted"
          actionHref="/upload"
        />
      </div>
    );
  }

  const { trend, scores, distribution } = buildChartData(items);
  const avg =
    scores.length > 0
      ? Math.round(scores.reduce((sum, s) => sum + s, 0) / scores.length)
      : null;
  const best = scores.length > 0 ? Math.round(Math.max(...scores)) : null;
  const failedCount = items.filter((item) => item.status === "failed").length;

  return (
    <div className="space-y-4">
      <PageHeader
        title="Analytics"
        description="What the experts have said about your resumes so far."
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile
          icon={<Flame className="size-4 text-primary" />}
          label="Roasts"
          value={String(roasts.data?.total ?? 0)}
          hint={failedCount > 0 ? `${failedCount} failed` : undefined}
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
      </div>

      <div className="rounded-2xl border border-border bg-card p-6">
        <h2 className="mb-4 font-semibold">Score trend</h2>
        {trend.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No scored roasts yet — still waiting on the first results.
          </p>
        ) : (
          <ChartContainer config={trendConfig} className="h-56 w-full">
            <AreaChart data={trend} margin={{ left: -20, right: 8 }}>
              <CartesianGrid vertical={false} strokeDasharray="3 3" />
              <XAxis dataKey="date" tickLine={false} axisLine={false} fontSize={12} />
              <YAxis domain={[0, 100]} tickLine={false} axisLine={false} fontSize={12} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Area
                dataKey="score"
                type="monotone"
                fill="var(--color-score)"
                fillOpacity={0.25}
                stroke="var(--color-score)"
                strokeWidth={2}
                dot={{ r: 3, fill: "var(--color-score)" }}
              />
            </AreaChart>
          </ChartContainer>
        )}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-border bg-card p-6">
          <h2 className="mb-4 font-semibold">Score distribution</h2>
          <ChartContainer config={distConfig} className="h-48 w-full">
            <BarChart data={distribution} margin={{ left: -24, right: 8 }}>
              <CartesianGrid vertical={false} strokeDasharray="3 3" />
              <XAxis dataKey="bucket" tickLine={false} axisLine={false} fontSize={12} />
              <YAxis allowDecimals={false} tickLine={false} axisLine={false} fontSize={12} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Bar
                dataKey="count"
                fill="var(--color-count)"
                radius={[6, 6, 0, 0]}
                maxBarSize={48}
              />
            </BarChart>
          </ChartContainer>
        </div>

        <div className="rounded-2xl border border-border bg-card p-6">
          <h2 className="mb-4 font-semibold">Recent activity</h2>
          <ActivityFeed items={items} />
        </div>
      </div>
    </div>
  );
}
