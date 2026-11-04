"use client";

import { motion, type Variants } from "framer-motion";
import {
  AlertTriangle,
  Check,
  Eye,
  Flame,
  Lightbulb,
  X,
} from "lucide-react";
import type { ReactNode } from "react";

import { ScoreRing } from "@/components/analysis/score-ring";
import { Badge } from "@/components/ui/badge";
import type {
  AnalysisResultPayload,
  AnalysisType,
  FixPlan,
  FixPlanItem,
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

/**
 * Long-form copy. Measure is owned by the card: the prose fills the content
 * box (no max-width cap), so the report uses the full width.
 */
const PROSE = "text-[15px] leading-[1.7]";

/**
 * Model prose arrives as one string with inconsistent newlines — sometimes
 * "\n\n", sometimes "\n". Rendered with whitespace-pre-wrap the gaps jump:
 * a blank line here, nothing there. Split on any newline and apply one
 * uniform paragraph gap instead.
 */
function RoastProse({ text, className }: { text: string; className?: string }) {
  const paragraphs = text
    .split(/\n+/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean);

  return (
    <div className={`${PROSE} ${className ?? ""}`}>
      {paragraphs.map((paragraph, index) => (
        <p key={index} className={index > 0 ? "mt-4" : ""}>
          {paragraph}
        </p>
      ))}
    </div>
  );
}

/** Small stamped label — used sparingly (one per section at most). */
const EYEBROW =
  "text-[11px] font-semibold uppercase tracking-[0.08em]";

function scoreColor(score: number): string {
  if (score >= 70) return "bg-primary";
  if (score >= 45) return "bg-amber-700 dark:bg-yellow-500";
  return "bg-destructive";
}

function scoreTextColor(score: number): string {
  if (score >= 70) return "text-primary";
  if (score >= 45) return "text-amber-700 dark:text-yellow-500";
  return "text-destructive";
}

function categoryByName(
  result: AnalysisResultPayload,
  name: string,
) {
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
      className={`rounded-lg border p-3 ${
        locked
          ? "border-border bg-muted/30 opacity-70"
          : "border-border bg-card"
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <span className="min-w-0 text-[11px] font-semibold tracking-[0.06em] text-muted-foreground uppercase">
          {label}
        </span>
        {weight !== null && (
          <span className="shrink-0 text-[11px] whitespace-nowrap text-muted-foreground">
            Weight {Math.round(weight * 100)}%
          </span>
        )}
      </div>
      {locked ? (
        <>
          <p className="mt-2 text-xl font-bold text-muted-foreground">— / 100</p>
          <p className="mt-0.5 text-xs text-muted-foreground">{lockedHint}</p>
        </>
      ) : (
        <>
          <p className={`mt-1 text-xl font-bold ${scoreTextColor(score ?? 0)}`}>
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
  action,
}: {
  result: AnalysisResultPayload;
  verdict: ScoreVerdict | null;
  action?: ReactNode;
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
    <div className="relative overflow-hidden rounded-xl border border-border bg-card p-5 sm:p-6">
      <div
        className="bg-glow-ember pointer-events-none absolute inset-x-0 -top-24 h-48"
        aria-hidden
      />
      <div className="relative">
        <p className={`${EYEBROW} text-primary`}>Diagnostic overview</p>
        <div className="mt-1 flex flex-wrap items-start justify-between gap-3">
          <h1 className="text-2xl font-bold tracking-tight">
            Resume Performance Scorecard
          </h1>
          {action}
        </div>
        <p className="mt-1 font-mono text-[11px] text-muted-foreground">
          Benchmark: senior engineering cohort, 2026 market
        </p>

        {/* Ring beside the cards only when both fit (xl+); below that the
            ring stacks so the cards never drop below their min text width. */}
        <div className="mt-4 grid gap-4 xl:grid-cols-[auto_minmax(0,1fr)] xl:items-center">
          <div className="flex flex-col items-center">
            <ScoreRing score={score} size={120} />
            {verdict && (
              <p
                className={`mt-2 text-sm font-bold ${scoreTextColor(score)}`}
              >
                {verdict.label}
              </p>
            )}
            <p className="mt-1 max-w-[26ch] text-center text-xs text-muted-foreground">
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
  "billable fit with caveats": "border-teal-500/40 bg-teal-500/10 text-teal-600 dark:text-teal-500",
  "borderline / screen fail": "border-amber-600/40 bg-amber-600/10 text-amber-700 dark:border-yellow-500/40 dark:bg-yellow-500/10 dark:text-yellow-500",
  "high rejection risk": "border-destructive/40 bg-destructive/10 text-destructive",
};

function RealityCheck({ result }: { result: AnalysisResultPayload }) {
  const check = result.reality_check;
  if (!check) return null;

  return (
    <motion.div
      variants={fadeUp}
      className="overflow-hidden rounded-xl border border-primary/25 bg-card"
    >
      <div className="relative p-5 sm:p-6">
        <div
          className="bg-glow-ember pointer-events-none absolute inset-x-0 -top-20 h-40"
          aria-hidden
        />
        <div className="relative">
          <p className={`${EYEBROW} text-primary`}>
            Unfiltered recruiter reality check
          </p>
          <h2 className="mt-2 max-w-[52ch] text-2xl font-bold tracking-tight">
            {check.headline_verdict}
          </h2>
          <p className={`mt-2 text-muted-foreground ${PROSE}`}>
            {check.verdict_summary}
          </p>
        </div>

        <div className="relative mt-4 rounded-lg border border-primary/25 bg-primary/5 p-3.5">
          <p className={`flex items-center gap-2 ${EYEBROW} text-primary`}>
            <Eye className="size-3.5" aria-hidden /> 5-second recruiter first
            impression
          </p>
          <p className="mt-1.5 font-mono text-sm leading-6 italic">
            {check.five_second_impression}
          </p>
        </div>

        {check.poison_points.length > 0 && (
          <div className="relative mt-4">
            <p className={`mb-2 flex items-center gap-2 ${EYEBROW} text-destructive`}>
              <AlertTriangle className="size-3.5" aria-hidden />
              Fatal application poison points ({check.poison_points.length})
            </p>
            <div className="grid gap-2 sm:grid-cols-2">
              {check.poison_points.map((point, index) => (
                <div
                  key={index}
                  className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/5 p-2.5 text-sm"
                >
                  <X className="mt-0.5 size-4 shrink-0 text-destructive" aria-hidden />
                  {point}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-border p-5 sm:p-6">
        <h3 className="flex items-center gap-2 text-base font-bold tracking-tight">
          <Flame className="size-4 text-primary" aria-hidden />
          The roast
        </h3>
        <RoastProse text={check.roast} className="mt-2" />

        <h3 className="mt-6 text-base font-bold tracking-tight">
          Rejection probability across 3 core industry markets
        </h3>
        <p className="mt-1 text-sm text-muted-foreground">
          How hiring managers and automated filters judge this profile in
          different hiring ecosystems.
        </p>
        <div className="mt-3 grid gap-3 lg:grid-cols-3">
          {check.market_analysis.map((market) => (
            <div
              key={market.market}
              className="rounded-lg border border-border bg-muted/30 p-3"
            >
              <span className="block text-sm font-semibold">
                {market.market}
              </span>
              <span
                className={`mt-2 inline-block rounded border px-2 py-0.5 font-mono text-[10px] tracking-[0.06em] uppercase ${
                  MARKET_CHIP[market.verdict]
                }`}
              >
                {market.verdict}
              </span>
              <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                {market.analysis}
              </p>
              {market.missing_signals.length > 0 && (
                <ul className="mt-2 space-y-1 border-t border-border pt-2">
                  {market.missing_signals.map((signal, index) => (
                    <li
                      key={index}
                      className="rounded bg-muted px-2 py-1 font-mono text-[10px] text-muted-foreground"
                    >
                      {signal}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}

const TONE_ICON: Record<string, ReactNode> = {
  critical: <Flame className="size-4 text-destructive" aria-hidden />,
  warning: <AlertTriangle className="size-4 text-amber-700 dark:text-yellow-500" aria-hidden />,
};

/** All three finding groups in one card, split by rules. */
function Findings({ result }: { result: AnalysisResultPayload }) {
  const groups: Array<{
    title: string;
    items: ReportItem[];
    tone: "critical" | "warning" | "suggestion";
  }> = [
    { title: "Critical issues", items: result.critical_issues, tone: "critical" },
    { title: "Warnings", items: result.warnings, tone: "warning" },
    { title: "Fix these", items: result.suggestions, tone: "suggestion" },
  ];
  const visible = groups.filter((group) => group.items.length > 0);
  if (visible.length === 0) return null;

  return (
    <motion.div
      variants={fadeUp}
      className="rounded-xl border border-border bg-card p-5"
    >
      {visible.map((group, groupIndex) => (
        <section
          key={group.title}
          className={groupIndex > 0 ? "mt-4 border-t border-border pt-4" : ""}
        >
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold">
            {TONE_ICON[group.tone]}
            {group.title}
            <span className="ml-auto rounded-full bg-muted px-2 py-0.5 text-xs font-normal text-muted-foreground">
              {group.items.length}
            </span>
          </h3>
          <ul className="space-y-1">
            {group.items.map((item, index) => (
              <li
                key={index}
                className={`rounded-md px-2 py-1.5 text-sm ${
                  group.tone === "critical" ? "text-destructive" : "text-foreground"
                }`}
              >
                {item.text}
                <span className="ml-2 text-xs text-muted-foreground">
                  — {item.source}
                </span>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </motion.div>
  );
}

function Breakdown({ result }: { result: AnalysisResultPayload }) {
  const breakdown = result.breakdown;
  if (!breakdown) return null;

  return (
    <motion.div
      variants={fadeUp}
      className="rounded-xl border border-border bg-card p-5"
    >
      <h3 className="mb-2 text-sm font-semibold">Deterministic checks</h3>
      <ul className="space-y-1 text-xs text-muted-foreground">
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

const SEVERITY_CHIP: Record<FixPlanItem["severity"], string> = {
  critical: "border-destructive/40 bg-destructive/10 text-destructive",
  warning:
    "border-amber-600/40 bg-amber-600/10 text-amber-700 dark:border-yellow-500/40 dark:bg-yellow-500/10 dark:text-yellow-500",
  enhancement: "border-primary/40 bg-primary/10 text-primary",
};

const EVALUATOR_LABELS: Record<string, string> = {
  ats: "ATS",
  recruiter: "Recruiter",
  technical: "Technical",
  job_matcher: "Job matcher",
  content_quality: "Content quality",
  communication: "Communication",
};

function evaluatorLabel(name: string): string {
  return EVALUATOR_LABELS[name] ?? name.replace(/_/g, " ");
}

const FIX_PLAN_SUBTITLE: Record<AnalysisType, string> = {
  jd_based: "Tailored to the job posting you pasted",
  role_based: "Tuned to the target role",
  general: "Market-optimized rewrites",
  custom: "Focused on what you asked for",
};

/** The AI fix plan: each top issue with the original line and its rewrite. */
function FixPlanSection({ plan, mode }: { plan: FixPlan; mode: AnalysisType }) {
  return (
    <motion.div
      variants={fadeUp}
      className="overflow-hidden rounded-xl border border-primary/25 bg-card"
    >
      <div className="p-5 sm:p-6">
        <div className="flex flex-wrap items-center gap-2">
          <Badge
            variant="outline"
            className="border-primary/40 bg-primary/10 text-primary"
          >
            Fix plan
          </Badge>
          <Badge variant="outline" className="text-muted-foreground">
            AI-rewritten
          </Badge>
        </div>
        <h2 className="mt-2 text-xl font-bold tracking-tight">Optimize it</h2>
        <p className="mt-1 text-xs text-muted-foreground">
          {FIX_PLAN_SUBTITLE[mode]}
        </p>
        <p className={`mt-2 text-muted-foreground ${PROSE}`}>
          {plan.intro}
        </p>

        <div className="mt-4 space-y-3">
          {plan.fixes.map((fix) => (
            <div key={fix.issue} className="rounded-lg border border-border p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-sm font-semibold">{fix.issue}</span>
                <Badge
                  variant="outline"
                  className={`capitalize ${SEVERITY_CHIP[fix.severity]}`}
                >
                  {fix.severity}
                </Badge>
              </div>
              <div className="mt-2 grid gap-2 lg:grid-cols-2">
                <div className="rounded-md border border-destructive/30 bg-destructive/5 p-2.5">
                  <p className="flex items-center gap-1.5 text-[10px] font-semibold tracking-[0.06em] uppercase text-destructive">
                    <X className="size-3" aria-hidden />
                    Before
                  </p>
                  <p className="mt-1 text-sm">{fix.before}</p>
                </div>
                <div className="rounded-md border border-primary/30 bg-primary/5 p-2.5">
                  <p className="flex items-center gap-1.5 text-[10px] font-semibold tracking-[0.06em] uppercase text-primary">
                    <Check className="size-3" aria-hidden />
                    After
                  </p>
                  <p className="mt-1 text-sm">{fix.after}</p>
                </div>
              </div>
              <p className="mt-2 flex items-start gap-1.5 text-xs text-muted-foreground">
                <Lightbulb className="mt-0.5 size-3.5 shrink-0" aria-hidden />
                {fix.why}
              </p>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}

/** The full roast view — only rendered for fully completed analyses. */
export function RoastResult({
  result,
  verdict,
  analysisType,
  action,
}: {
  result: AnalysisResultPayload;
  verdict: ScoreVerdict | null;
  analysisType: AnalysisType;
  action?: ReactNode;
}) {
  return (
    <motion.div
      variants={stagger}
      initial="hidden"
      animate="show"
      className="space-y-3"
    >
      <motion.div variants={fadeUp}>
        <ScorecardHeader result={result} verdict={verdict} action={action} />
      </motion.div>

      {result.reality_check && <RealityCheck result={result} />}

      {result.fix_plan && (
        <FixPlanSection plan={result.fix_plan} mode={analysisType} />
      )}

      {result.final_roast && !result.reality_check && (
        <motion.div
          variants={fadeUp}
          className="relative overflow-hidden rounded-xl border border-primary/30 bg-primary/5 p-5"
        >
          <div
            className="bg-glow-ember pointer-events-none absolute -top-16 -right-16 size-48"
            aria-hidden
          />
          <h3 className="relative mb-2 flex items-center gap-2 text-base font-bold">
            <Flame className="size-4 text-primary" aria-hidden />
            The roast
          </h3>
          <RoastProse text={result.final_roast} className="relative" />
        </motion.div>
      )}

      <Findings result={result} />

      {result.positive_notes.length > 0 && (
        <motion.div
          variants={fadeUp}
          className="rounded-xl border border-border bg-card p-5"
        >
          <h3 className="mb-2 text-sm font-semibold">What works — keep it</h3>
          <ul className="space-y-1.5">
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
          className="rounded-xl border border-border bg-card p-5"
        >
          <h3 className="mb-1 text-sm font-semibold">Expert verdicts</h3>
          <div className="divide-y divide-border">
            {Object.entries(result.evaluator_summaries).map(([name, summary]) => (
              <div key={name} className="py-2.5">
                <p className="text-[11px] font-medium tracking-[0.06em] uppercase text-primary">
                  {evaluatorLabel(name)}
                </p>
                <p className="mt-0.5 text-sm">{summary}</p>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
