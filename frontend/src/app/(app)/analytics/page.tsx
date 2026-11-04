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
import { analysisModeLabel } from "@/lib/analysis-modes";
import { formatShortDate } from "@/lib/format";
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

function buildChartData(items: AnalysisListItem[]) {
  // API returns newest first — the trend reads oldest → newest.
  const scored = items
    .filter((item) => item.overall_score !== null)
    .reverse();
  const trend = scored.map((item) => ({
    date: formatShortDate(item.created_at),
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
    <ul className="space-y-2">
      {recent.map((item) => {
        const running = isRunningStatus(item.status);
        return (
          <li key={item.id} className="flex items-center gap-3">
            {item.overall_score !== null ? (
              <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary/12 text-xs font-bold text-primary tabular-nums">
                {Math.round(item.overall_score)}
              </span>
            ) : (
              <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-muted text-muted-foreground">
                <History className="size-4" />
              </span>
            )}
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm leading-5">
                {running ? (
                  <span>{analysisModeLabel(item.analysis_type)} analysis</span>
                ) : (
                  <Link
                    href={`/analysis/${item.id}`}
                    className="hover:text-primary hover:underline"
                  >
                    {analysisModeLabel(item.analysis_type)} analysis
                  </Link>
                )}
              </p>
              <p className="text-xs leading-4 text-muted-foreground">
                {formatShortDate(item.created_at)}
              </p>
            </div>
            {item.status !== "completed" && <StatusBadge status={item.status} />}
          </li>
        );
      })}
    </ul>
  );
}

export default function AnalyticsPage() {
  const roasts = useAnalyses();
  const resumes = useResumes();

  const header = (
    <PageHeader
      title="Analytics"
      description="What the experts have said about your resumes so far."
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
        <Skeleton className="h-64 rounded-xl" />
      </div>
    );
  }

  if (roasts.isError) {
    return (
      <div className="space-y-6">
        {header}
        <ErrorState
          title="Could not load analytics"
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
    <div className="space-y-6">
      {header}

      <div className="grid auto-rows-fr grid-cols-2 gap-2 sm:gap-3 lg:grid-cols-4">
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

      <div className="rounded-xl border border-border bg-card p-5">
        <h2 className="mb-3 text-sm font-semibold">Score trend</h2>
        {trend.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No scored roasts yet — still waiting on the first results.
          </p>
        ) : (
          <ChartContainer
            config={trendConfig}
            className="h-56 w-full [&_.recharts-area-area]:fill-chart-1 [&_.recharts-area-curve]:stroke-chart-1 [&_.recharts-area-dot]:fill-chart-1 [&_.recharts-area-dot]:stroke-chart-1"
          >
            <AreaChart data={trend} margin={{ left: -20, right: 8 }}>
              <CartesianGrid vertical={false} strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickLine={false}
                axisLine={false}
                fontSize={12}
                // Several roasts can share a day: label the first point of
                // each day and leave the repeats blank so the axis is readable.
                tickFormatter={(value: string, index: number) =>
                  index > 0 && trend[index - 1]?.date === value ? "" : value
                }
              />
              <YAxis domain={[0, 100]} tickLine={false} axisLine={false} fontSize={12} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Area
                dataKey="score"
                type="monotone"
                fillOpacity={0.25}
                strokeWidth={2}
                dot={{ r: 3 }}
                isAnimationActive={false}
              />
            </AreaChart>
          </ChartContainer>
        )}
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        <div className="rounded-xl border border-border bg-card p-5">
          <h2 className="mb-3 text-sm font-semibold">Score distribution</h2>
          <ChartContainer config={distConfig} className="h-48 w-full">
            <BarChart data={distribution} margin={{ left: -24, right: 8 }}>
              <CartesianGrid vertical={false} strokeDasharray="3 3" />
              <XAxis dataKey="bucket" tickLine={false} axisLine={false} fontSize={12} />
              <YAxis allowDecimals={false} tickLine={false} axisLine={false} fontSize={12} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Bar
                dataKey="count"
                className="fill-chart-1"
                radius={[6, 6, 0, 0]}
                maxBarSize={48}
                isAnimationActive={false}
              />
            </BarChart>
          </ChartContainer>
        </div>

        <div className="rounded-xl border border-border bg-card p-5">
          <h2 className="mb-3 text-sm font-semibold">Recent activity</h2>
          <ActivityFeed items={items} />
        </div>
      </div>
    </div>
  );
}
