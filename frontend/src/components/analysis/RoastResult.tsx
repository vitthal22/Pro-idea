"use client";

import { motion, type Variants } from "framer-motion";
import { AlertTriangle, Check, Crosshair, Flame } from "lucide-react";

import { ScoreRing } from "@/components/analysis/score-ring";
import { Badge } from "@/components/ui/badge";
import type {
  AnalysisResultPayload,
  AnalysisStatus,
  CategoryScore,
  JobMatchFeedback,
  ReportItem,
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
    <div className="relative overflow-hidden rounded-2xl border border-border bg-card p-8 text-center">
      <div className="bg-glow-ember pointer-events-none absolute inset-x-0 -top-24 h-48" aria-hidden />
      <p className="relative text-sm text-muted-foreground">Your roast score</p>
      <div className="relative mt-3 flex justify-center">
        <ScoreRing score={score} size={140} />
      </div>
      <p className="relative mt-2 text-sm text-muted-foreground">out of 100</p>
      {result.breakdown && (
        <p className="relative mt-1 text-xs text-muted-foreground">
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

function JobMatchCard({ feedback }: { feedback: JobMatchFeedback }) {
  return (
    <motion.div
      variants={fadeUp}
      className="rounded-2xl border border-border bg-card p-6"
    >
      <h3 className="mb-3 flex items-center gap-2 font-semibold">
        <Crosshair className="size-4 text-primary" aria-hidden />
        Job match
        <span className="ml-auto text-sm font-normal capitalize text-primary">
          {feedback.match_rating}
        </span>
      </h3>
      <p className="text-sm text-muted-foreground">{feedback.summary}</p>

      {feedback.matched_skills.length > 0 && (
        <div className="mt-4">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Matched
          </p>
          <div className="mt-1.5 flex flex-wrap gap-1.5">
            {feedback.matched_skills.map((skill) => (
              <Badge key={skill} variant="secondary">
                {skill}
              </Badge>
            ))}
          </div>
        </div>
      )}
      {feedback.missing_skills.length > 0 && (
        <div className="mt-3">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Missing
          </p>
          <div className="mt-1.5 flex flex-wrap gap-1.5">
            {feedback.missing_skills.map((skill) => (
              <Badge key={skill} variant="destructive">
                {skill}
              </Badge>
            ))}
          </div>
        </div>
      )}
      {feedback.recommendations.length > 0 && (
        <ul className="mt-4 space-y-1.5 border-t border-border pt-3">
          {feedback.recommendations.map((rec, index) => (
            <li key={index} className="text-sm">
              {rec}
            </li>
          ))}
        </ul>
      )}
    </motion.div>
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
    <motion.div
      variants={stagger}
      initial="hidden"
      animate="show"
      className="space-y-5"
    >
      {partial && (
        <motion.div
          variants={fadeUp}
          className="flex items-start gap-3 rounded-xl border border-yellow-500/40 bg-yellow-500/10 p-4 text-sm"
        >
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-yellow-500" aria-hidden />
          <span>
            Partial analysis
            {result.failed_evaluators.length > 0 &&
              ` — unavailable: ${result.failed_evaluators.join(", ")}`}
            {result.roast_fallback_used &&
              " — the narrative roast pass fell back to a raw summary"}
            . The score is based on the surviving reviews.
          </span>
        </motion.div>
      )}

      <motion.div variants={fadeUp}>
        <ScoreHeader result={result} />
      </motion.div>

      {result.final_roast && (
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
      {result.job_match_feedback && (
        <JobMatchCard feedback={result.job_match_feedback} />
      )}
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
