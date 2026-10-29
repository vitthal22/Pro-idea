"use client";

import { motion, type Variants } from "framer-motion";
import {
  AlertTriangle,
  Check,
  Eye,
  Flame,
  X,
} from "lucide-react";

import { ScoreRing } from "@/components/analysis/score-ring";
import { Badge } from "@/components/ui/badge";
import type {
  AnalysisResultPayload,
  CategoryScore,
  MarketVerdict,
  ReportItem,
  ScoreVerdict,
} from "@/types/analysis";

const stagger: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06 } },
};
const fadeUp: Variants = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: "easeOut" } },
};

const CATEGORY_LABELS: Record<string, string> = {
  content_quality: "Impact & Language",
  experience: "Experience",
  skills_alignment: "Skills alignment",
  ats_compatibility: "ATS Compatibility",
  role_relevance: "Job Match",
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

function scoreTextColor(score: number): string {
  if (score >= 70) return "text-primary";
  if (score >= 45) return "text-yellow-500";
  return "text-destructive";
}

function categoryByName(
  result: AnalysisResultPayload,
  name: string,
): CategoryScore | undefined {
  return result.breakdown?.ai_categories.find((c) => c.category === name);
}

/** Weighted category card from the reference scorecard design. */
function CategoryCard({
  label,
  weight,
  score,
  locked,
  lockedHint,
}: {
  label: string;
  weight: number | null;
  score: number | null;
  locked?: boolean;
  lockedHint?: string;
}) {
  return (
    <div
      className={`rounded-xl border p-4 ${
        locked
          ? "border-border bg-muted/30 opacity-70"
          : "border-border bg-card"
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <span className="min-w-0 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          {label}
        </span>
        {weight !== null && (
          <span className="shrink-0 whitespace-nowrap text-[11px] text-muted-foreground">
            Weight {Math.round(weight * 100)}%
          </span>
        )}
      </div>
      {locked ? (
        <>
          <p className="mt-2 text-2xl font-bold text-muted-foreground">— / 100</p>
          <p className="mt-1 text-xs text-muted-foreground">{lockedHint}</p>
        </>
      ) : (
        <>
          <p className={`mt-1 text-2xl font-bold ${scoreTextColor(score ?? 0)}`}>
            {Math.round(score ?? 0)}
            <span className="ml-1 text-xs font-normal text-muted-foreground">
              out of 100
            </span>
          </p>
          <div className="mt-2 h-1.5 rounded-full bg-muted">
            <motion.div
              className={`h-1.5 rounded-full ${scoreColor(score ?? 0)}`}
              initial={{ width: 0 }}
              animate={{ width: `${score ?? 0}%` }}
              transition={{ duration: 0.9, ease: "easeOut", delay: 0.25 }}
            />
          </div>
        </>
      )}
    </div>
  );
}

function ScorecardHeader({
  result,
  verdict,
}: {
  result: AnalysisResultPayload;
  verdict: ScoreVerdict | null;
}) {
  const score = result.overall_score ?? 0;
  const ats = categoryByName(result, "ats_compatibility");
  const impact = categoryByName(result, "content_quality");
  const jobMatch = categoryByName(result, "role_relevance");
  const completeness = result.breakdown?.deterministic_checks.find(
    (c) => c.name === "section_completeness",
  );
  const completenessScore = completeness
    ? (completeness.score / completeness.max) * 100
    : null;
  const hasJobMatch = result.job_match_feedback !== null && jobMatch !== undefined;

  return (
    <div className="relative overflow-hidden rounded-2xl border border-border bg-card p-6 sm:p-8">
      <div
        className="bg-glow-ember pointer-events-none absolute inset-x-0 -top-24 h-48"
        aria-hidden
      />
      <div className="relative">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-primary">
          Diagnostic Overview
        </p>
        <div className="mt-1 flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="text-2xl font-bold tracking-tight">
            Resume Performance Scorecard
          </h2>
          <span className="font-mono text-[11px] text-muted-foreground">
            Benchmark: senior engineering cohort, 2026 market
          </span>
        </div>

        {/* Ring beside the cards only when both fit (xl+); below that the
            ring stacks so the cards never drop below their min text width. */}
        <div className="mt-6 grid gap-6 xl:grid-cols-[auto_minmax(0,1fr)] xl:items-center">
          <div className="flex flex-col items-center">
            <ScoreRing score={score} size={150} />
            {verdict && (
              <p
                className={`mt-2 text-sm font-bold ${scoreTextColor(score)}`}
              >
                {verdict.label}
              </p>
            )}
            <p className="mt-1 max-w-xs text-center text-xs text-muted-foreground">
              {verdict?.line}
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <CategoryCard
              label="ATS Compatibility"
              weight={ats?.weight ?? null}
              score={ats?.score ?? null}
            />
            <CategoryCard
              label="Job Match"
              weight={hasJobMatch ? (jobMatch?.weight ?? null) : null}
              score={hasJobMatch ? (jobMatch?.score ?? null) : null}
              locked={!hasJobMatch}
              lockedHint="Run a role or JD roast to unlock"
            />
            <CategoryCard
              label="Impact & Language"
              weight={impact?.weight ?? null}
              score={impact?.score ?? null}
            />
            <CategoryCard
              label="Completeness"
              weight={null}
              score={completenessScore}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

const MARKET_CHIP: Record<MarketVerdict["verdict"], string> = {
  "strong fit": "border-primary/40 bg-primary/10 text-primary",
  "billable fit with caveats": "border-teal-500/40 bg-teal-500/10 text-teal-500",
  "borderline / screen fail": "border-yellow-500/40 bg-yellow-500/10 text-yellow-500",
  "high rejection risk": "border-destructive/40 bg-destructive/10 text-destructive",
};

function RealityCheck({ result }: { result: AnalysisResultPayload }) {
  const check = result.reality_check;
  if (!check) return null;

  return (
    <motion.div
      variants={fadeUp}
      className="overflow-hidden rounded-2xl border border-primary/25 bg-card"
    >
      <div className="relative p-6 sm:p-8">
        <div
          className="bg-glow-ember pointer-events-none absolute inset-x-0 -top-20 h-40"
          aria-hidden
        />
        <div className="relative">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <Badge variant="outline" className="border-primary/40 font-mono text-[10px] uppercase tracking-[0.2em] text-primary">
              Unfiltered Recruiter Reality Check
            </Badge>
            <Badge
              variant="outline"
              className="border-destructive/40 font-mono text-[10px] uppercase tracking-widest text-destructive"
            >
              Zero-Sugarcoating Mode
            </Badge>
          </div>
          <h2 className="mt-3 text-2xl font-bold tracking-tight sm:text-3xl">
            {check.headline_verdict}
          </h2>
          <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
            {check.verdict_summary}
          </p>
        </div>

        <div className="relative mt-6 rounded-xl border border-primary/25 bg-primary/5 p-4">
          <p className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.15em] text-primary">
            <Eye className="size-3.5" aria-hidden />
            5-second recruiter first impression (why you get passed over)
          </p>
          <p className="mt-2 font-mono text-sm italic leading-relaxed">
            {check.five_second_impression}
          </p>
        </div>

        {check.poison_points.length > 0 && (
          <div className="relative mt-6">
            <p className="mb-2 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.15em] text-destructive">
              <AlertTriangle className="size-3.5" aria-hidden />
              Fatal application poison points ({check.poison_points.length})
            </p>
            <div className="grid gap-2 sm:grid-cols-2">
              {check.poison_points.map((point, index) => (
                <div
                  key={index}
                  className="flex items-start gap-2 rounded-xl border border-destructive/30 bg-destructive/5 p-3 text-sm"
                >
                  <X className="mt-0.5 size-4 shrink-0 text-destructive" aria-hidden />
                  {point}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-border p-6 sm:p-8">
        <h3 className="flex items-center gap-2 text-lg font-bold tracking-tight">
          <Flame className="size-4 text-primary" aria-hidden />
          The roast
        </h3>
        <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed">
          {check.roast}
        </p>

        <h3 className="mt-8 text-lg font-bold tracking-tight">
          Rejection probability across 3 core industry markets
        </h3>
        <p className="mt-1 text-sm text-muted-foreground">
          How hiring managers and automated filters judge this profile in
          different hiring ecosystems.
        </p>
        <div className="mt-4 grid gap-3 lg:grid-cols-3">
          {check.market_analysis.map((market) => (
            <div
              key={market.market}
              className="rounded-xl border border-border bg-muted/30 p-4"
            >
              <div className="flex items-start justify-between gap-2">
                <span className="text-sm font-semibold">{market.market}</span>
              </div>
              <span
                className={`mt-2 inline-block rounded-md border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider ${
                  MARKET_CHIP[market.verdict]
                }`}
              >
                {market.verdict}
              </span>
              <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
                {market.analysis}
              </p>
              {market.missing_signals.length > 0 && (
                <div className="mt-3 border-t border-border pt-2">
                  <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                    Missing signals:
                  </p>
                  <ul className="mt-1.5 space-y-1">
                    {market.missing_signals.map((signal, index) => (
                      <li
                        key={index}
                        className="rounded bg-muted px-2 py-1 font-mono text-[10px] text-muted-foreground"
                      >
                        {signal}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </motion.div>
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
    <motion.div
      variants={fadeUp}
      className="rounded-2xl border border-border bg-card p-6"
    >
      <h3 className="mb-3 flex items-center gap-2 font-semibold">
        {tone === "critical" && (
          <Flame className="size-4 text-destructive" aria-hidden />
        )}
        {tone === "warning" && (
          <AlertTriangle className="size-4 text-yellow-500" aria-hidden />
        )}
        {title}
        <span className="ml-auto rounded-full bg-muted px-2 py-0.5 text-xs font-normal text-muted-foreground">
          {items.length}
        </span>
      </h3>
      <motion.ul variants={stagger} initial="hidden" animate="show" className="space-y-2">
        {items.map((item, index) => (
          <motion.li
            key={index}
            variants={fadeUp}
            className="rounded-lg px-3 py-2 text-sm transition-colors hover:bg-muted/50"
          >
            <span
              className={tone === "critical" ? "text-destructive" : "text-foreground"}
            >
              {item.text}
            </span>
            <span className="ml-2 text-xs text-muted-foreground">
              — {item.source}
            </span>
          </motion.li>
        ))}
      </motion.ul>
    </motion.div>
  );
}

function Breakdown({ result }: { result: AnalysisResultPayload }) {
  const breakdown = result.breakdown;
  if (!breakdown) return null;

  return (
    <motion.div
      variants={fadeUp}
      className="rounded-2xl border border-border bg-card p-6"
    >
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
              <motion.div
                className={`h-2 rounded-full ${scoreColor(category.score)}`}
                initial={{ width: 0 }}
                animate={{ width: `${category.score}%` }}
                transition={{ duration: 0.9, ease: "easeOut", delay: 0.2 }}
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
    </motion.div>
  );
}

/** The full roast view — only rendered for fully completed analyses. */
export function RoastResult({
  result,
  verdict,
}: {
  result: AnalysisResultPayload;
  verdict: ScoreVerdict | null;
}) {
  return (
    <motion.div
      variants={stagger}
      initial="hidden"
      animate="show"
      className="space-y-5"
    >
      <motion.div variants={fadeUp}>
        <ScorecardHeader result={result} verdict={verdict} />
      </motion.div>

      {result.reality_check && (
        <RealityCheck result={result} />
      )}

      {result.final_roast && !result.reality_check && (
        <motion.div
          variants={fadeUp}
          className="relative overflow-hidden rounded-2xl border border-primary/30 bg-primary/5 p-6"
        >
          <div
            className="bg-glow-ember pointer-events-none absolute -right-16 -top-16 size-48"
            aria-hidden
          />
          <h3 className="relative mb-3 flex items-center gap-2 font-semibold">
            <Flame className="size-4 text-primary" aria-hidden />
            The roast
          </h3>
          <p className="relative whitespace-pre-wrap text-sm leading-relaxed">
            {result.final_roast}
          </p>
        </motion.div>
      )}

      <FindingsList
        title="Critical issues"
        items={result.critical_issues}
        tone="critical"
      />
      <FindingsList title="Warnings" items={result.warnings} tone="warning" />
      <FindingsList
        title="Fix these"
        items={result.suggestions}
        tone="suggestion"
      />

      {result.positive_notes.length > 0 && (
        <motion.div
          variants={fadeUp}
          className="rounded-2xl border border-border bg-card p-6"
        >
          <h3 className="mb-3 font-semibold">What works — keep it</h3>
          <ul className="space-y-2">
            {result.positive_notes.map((note, index) => (
              <li key={index} className="flex gap-2 text-sm">
                <Check className="mt-0.5 size-4 shrink-0 text-primary" />
                {note}
              </li>
            ))}
          </ul>
        </motion.div>
      )}

      <Breakdown result={result} />

      {Object.keys(result.evaluator_summaries).length > 0 && (
        <motion.div
          variants={fadeUp}
          className="rounded-2xl border border-border bg-card p-6"
        >
          <h3 className="mb-3 font-semibold">Expert verdicts</h3>
          <div className="grid gap-3 sm:grid-cols-2">
            {Object.entries(result.evaluator_summaries).map(([name, summary]) => (
              <div key={name} className="rounded-xl border border-border p-3">
                <p className="text-xs font-medium uppercase tracking-wide text-primary">
                  {name}
                </p>
                <p className="mt-1 text-sm">{summary}</p>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
