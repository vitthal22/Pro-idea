"use client";

import { AlertTriangle, Check, Flame } from "lucide-react";

import type {
  AnalysisResultPayload,
  AnalysisStatus,
  CategoryScore,
  ReportItem,
} from "@/types/analysis";

const CATEGORY_LABELS: Record<string, string> = {
  content_quality: "Content quality",
  experience: "Experience",
  skills_alignment: "Skills alignment",
  ats_compatibility: "ATS compatibility",
  role_relevance: "Role relevance",
};

function categoryLabel(category: string): string {
  return (
    CATEGORY_LABELS[category] ??
    category.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase())
  );
}

function scoreColor(score: number): string {
  if (score >= 70) return "bg-primary";
  if (score >= 45) return "bg-yellow-500";
  return "bg-destructive";
}

function ScoreHeader({ result }: { result: AnalysisResultPayload }) {
  const score = result.overall_score ?? 0;
  return (
    <div className="rounded-2xl border border-border bg-card p-6 text-center">
      <p className="text-sm text-muted-foreground">Your roast score</p>
      <p
        className={`mt-1 text-6xl font-bold ${
          score >= 70 ? "text-primary" : score >= 45 ? "text-yellow-500" : "text-destructive"
        }`}
      >
        {Math.round(score)}
      </p>
      <p className="text-sm text-muted-foreground">out of 100</p>
      {result.breakdown && (
        <p className="mt-2 text-xs text-muted-foreground">
          {Math.round(result.breakdown.deterministic_score)} from deterministic
          checks • {Math.round(result.breakdown.ai_score)} from expert ratings
        </p>
      )}
    </div>
  );
}

function FindingsList({
  title,
  items,
  tone,
}: {
  title: string;
  items: ReportItem[];
  tone: "critical" | "warning" | "suggestion";
}) {
  if (items.length === 0) return null;
  return (
    <div className="rounded-2xl border border-border bg-card p-6">
      <h3 className="mb-3 flex items-center gap-2 font-semibold">
        {tone === "critical" && (
          <Flame className="size-4 text-destructive" aria-hidden />
        )}
        {tone === "warning" && (
          <AlertTriangle className="size-4 text-yellow-500" aria-hidden />
        )}
        {title}
        <span className="ml-auto text-sm font-normal text-muted-foreground">
          {items.length}
        </span>
      </h3>
      <ul className="space-y-2">
        {items.map((item, index) => (
          <li key={index} className="text-sm">
            <span
              className={
                tone === "critical" ? "text-destructive" : "text-foreground"
              }
            >
              {item.text}
            </span>
            <span className="ml-2 text-xs text-muted-foreground">
              — {item.source}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Breakdown({
  result,
}: {
  result: AnalysisResultPayload;
}) {
  const breakdown = result.breakdown;
  if (!breakdown) return null;

  return (
    <div className="rounded-2xl border border-border bg-card p-6">
      <h3 className="mb-4 font-semibold">Score breakdown</h3>

      <div className="space-y-3">
        {breakdown.ai_categories.map((category: CategoryScore) => (
          <div key={category.category}>
            <div className="mb-1 flex items-center justify-between text-sm">
              <span>{categoryLabel(category.category)}</span>
              <span className="text-muted-foreground">
                {category.rating} • {Math.round(category.score)}
              </span>
            </div>
            <div className="h-2 rounded-full bg-muted">
              <div
                className={`h-2 rounded-full ${scoreColor(category.score)}`}
                style={{ width: `${category.score}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      <ul className="mt-5 space-y-1 border-t border-border pt-4 text-xs text-muted-foreground">
        {breakdown.deterministic_checks.map((check) => (
          <li key={check.name} className="flex justify-between gap-4">
            <span>
              {check.name.replace(/_/g, " ")} — {check.details}
            </span>
            <span className="shrink-0 font-medium">
              {check.score}/{check.max}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/** The full roast view once the pipeline reaches completed/partial. */
export function RoastResult({
  status,
  result,
}: {
  status: AnalysisStatus;
  result: AnalysisResultPayload;
}) {
  const partial =
    status === "partial" ||
    result.failed_evaluators.length > 0 ||
    result.roast_fallback_used;

  return (
    <div className="space-y-5">
      {partial && (
        <div className="rounded-xl border border-yellow-500/50 bg-yellow-500/10 p-4 text-sm">
          Partial analysis
          {result.failed_evaluators.length > 0 &&
            ` — unavailable: ${result.failed_evaluators.join(", ")}`}
          {result.roast_fallback_used &&
            " — the narrative roast pass fell back to a raw summary"}
          . The score is based on the surviving reviews.
        </div>
      )}

      <ScoreHeader result={result} />

      {result.final_roast && (
        <div className="rounded-2xl border border-primary/40 bg-primary/5 p-6">
          <h3 className="mb-3 flex items-center gap-2 font-semibold">
            <Flame className="size-4 text-primary" aria-hidden />
            The roast
          </h3>
          <p className="whitespace-pre-wrap text-sm leading-relaxed">
            {result.final_roast}
          </p>
        </div>
      )}

      <FindingsList
        title="Critical issues"
        items={result.critical_issues}
        tone="critical"
      />
      <FindingsList
        title="Warnings"
        items={result.warnings}
        tone="warning"
      />
      <FindingsList
        title="Fix these"
        items={result.suggestions}
        tone="suggestion"
      />

      {result.positive_notes.length > 0 && (
        <div className="rounded-2xl border border-border bg-card p-6">
          <h3 className="mb-3 font-semibold">What works — keep it</h3>
          <ul className="space-y-2">
            {result.positive_notes.map((note, index) => (
              <li key={index} className="flex gap-2 text-sm">
                <Check className="mt-0.5 size-4 shrink-0 text-primary" />
                {note}
              </li>
            ))}
          </ul>
        </div>
      )}

      <Breakdown result={result} />

      {Object.keys(result.evaluator_summaries).length > 0 && (
        <div className="rounded-2xl border border-border bg-card p-6">
          <h3 className="mb-3 font-semibold">Expert verdicts</h3>
          <div className="grid gap-3 sm:grid-cols-2">
            {Object.entries(result.evaluator_summaries).map(([name, summary]) => (
              <div key={name} className="rounded-xl border border-border p-3">
                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  {name}
                </p>
                <p className="mt-1 text-sm">{summary}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
