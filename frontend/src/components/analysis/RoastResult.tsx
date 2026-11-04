"use client";

import { AlertTriangle, ArrowLeft, ArrowRight, Check, ChevronDown, Eye, Flame } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { analysisModeLabel } from "@/lib/analysis-modes";
import { cn } from "@/lib/utils";
import type {
  AnalysisResultPayload,
  AnalysisType,
  FixPlanItem,
  MarketVerdict,
  ReportItem,
  ScoreVerdict,
} from "@/types/analysis";

const EYEBROW =
  "font-mono text-[11px] font-medium tracking-[0.08em] uppercase text-muted-foreground";

const CHIP =
  "inline-block rounded-sm border px-2 py-0.5 font-mono text-[10px] tracking-[0.06em] uppercase";

/** Model prose: one paragraph per block, uniform gap. */
const PROSE = "text-[15px] leading-[1.7]";

function pad(value: number): string {
  return String(value).padStart(2, "0");
}

/** Score tone, aligned with the backend verdict bands (80 / 65 / 45). */
function tone(score: number) {
  if (score >= 80) {
    return { text: "text-pass", bar: "bg-pass", chip: "border-pass/40 text-pass" };
  }
  if (score >= 65) {
    return {
      text: "text-primary",
      bar: "bg-primary",
      chip: "border-primary/40 text-primary",
    };
  }
  if (score >= 45) {
    return {
      text: "text-amber-700 dark:text-yellow-500",
      bar: "bg-amber-700 dark:bg-yellow-500",
      chip:
        "border-amber-700/40 text-amber-700 dark:border-yellow-500/40 dark:text-yellow-500",
    };
  }
  return {
    text: "text-destructive",
    bar: "bg-destructive",
    chip: "border-destructive/40 text-destructive",
  };
}

/** Reveal on first scroll into view; visible by default (SSR safe). */
function Reveal({ children, className }: { children: ReactNode; className?: string }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (element.getBoundingClientRect().top < window.innerHeight * 0.85) return;

    element.classList.add("reveal-hidden");
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          element.classList.remove("reveal-hidden");
          element.classList.add("reveal-shown");
          observer.disconnect();
        }
      },
      { threshold: 0.12 },
    );
    observer.observe(element);

    return () => {
      observer.disconnect();
      element.classList.remove("reveal-hidden");
    };
  }, []);

  return (
    <div ref={ref} className={className}>
      {children}
    </div>
  );
}

function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn("rounded-xl border border-border bg-card p-4", className)}>
      {children}
    </div>
  );
}

function SectionLabel({
  number,
  title,
  meta,
}: {
  number: string;
  title: string;
  meta?: ReactNode;
}) {
  return (
    <div className="mt-6 mb-2 flex flex-wrap items-baseline gap-3">
      <span className="font-mono text-[11px] text-muted-foreground/60">{number}</span>
      <h2 className="text-xl font-semibold tracking-tight">{title}</h2>
      {meta && <div className="ml-auto">{meta}</div>}
    </div>
  );
}

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

/** 0–100 track with the four real verdict zones and a marker at the score. */
function ScoreStrip({ score }: { score: number }) {
  const zones = [
    { from: 0, to: 45, className: "bg-destructive/70" },
    { from: 45, to: 65, className: "bg-amber-600/70" },
    { from: 65, to: 80, className: "bg-primary" },
    { from: 80, to: 100, className: "bg-pass/70" },
  ];
  const position = Math.min(100, Math.max(0, score));

  return (
    <div className="relative mt-4">
      <div className="relative h-1.5 w-full overflow-hidden rounded-full bg-muted">
        {zones.map((zone) => (
          <div
            key={zone.to}
            className={`absolute inset-y-0 ${zone.className}`}
            style={{ left: `${zone.from}%`, width: `${zone.to - zone.from}%` }}
          />
        ))}
      </div>
      <div
        className="absolute -top-1 h-3.5 w-0.5 bg-foreground"
        style={{ left: `calc(${position}% - 1px)` }}
        title={`Score ${score} of 100`}
      />
      <div className="relative mt-1 h-3 text-[10px] text-muted-foreground">
        {[45, 65, 80].map((tick) => (
          <span
            key={tick}
            className="absolute -translate-x-1/2 font-mono"
            style={{ left: `${tick}%` }}
          >
            {tick}
          </span>
        ))}
      </div>
    </div>
  );
}

/** Deterministic checks and AI evaluators, 50 / 50 of the total. */
function CompositionBar({ result }: { result: AnalysisResultPayload }) {
  const breakdown = result.breakdown;
  if (!breakdown) return null;

  const deterministic = Math.round(breakdown.deterministic_score * 0.5);
  const ai = Math.round(breakdown.ai_score * 0.5);

  return (
    <div className="mt-2">
      <div className="flex h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <div className="h-full bg-muted-foreground/45" style={{ width: `${deterministic}%` }} />
        <div className="h-full bg-primary" style={{ width: `${ai}%` }} />
      </div>
      <p className="mt-1 font-mono text-[10px] text-muted-foreground">
        Deterministic {deterministic} + AI {ai} = {deterministic + ai}
      </p>
    </div>
  );
}

/** Critical / warnings / fixes as one bar. */
function SeverityStrip({ result }: { result: AnalysisResultPayload }) {
  const critical = result.critical_issues.length;
  const warnings = result.warnings.length;
  const fixes = result.suggestions.length;
  const total = critical + warnings + fixes;
  if (total === 0) return null;

  return (
    <div className="flex items-center gap-2">
      <div className="flex h-1.5 w-24 overflow-hidden rounded-full bg-muted">
        <div className="bg-destructive" style={{ width: `${(critical / total) * 100}%` }} />
        <div
          className="bg-amber-600 dark:bg-yellow-500"
          style={{ width: `${(warnings / total) * 100}%` }}
        />
        <div
          className="bg-muted-foreground/45"
          style={{ width: `${(fixes / total) * 100}%` }}
        />
      </div>
      <span className="font-mono text-[10px] text-muted-foreground">
        {critical} · {warnings} · {fixes}
      </span>
    </div>
  );
}

/** Score + band strip + the four categories + how the total was built. */
function HeroCard({
  result,
  verdict,
  large = false,
}: {
  result: AnalysisResultPayload;
  verdict: ScoreVerdict | null;
  large?: boolean;
}) {
  const score = Math.round(result.overall_score ?? 0);
  const band = tone(score);

  const category = (name: string) =>
    result.breakdown?.ai_categories.find((entry) => entry.category === name);
  const ats = category("ats_compatibility");
  const impact = category("content_quality");
  const jobMatch = category("role_relevance");
  const completeness = result.breakdown?.deterministic_checks.find(
    (check) => check.name === "section_completeness",
  );
  const completenessScore = completeness
    ? Math.round((completeness.score / completeness.max) * 100)
    : null;
  const hasJobMatch = result.job_match_feedback !== null && jobMatch !== undefined;

  const metrics = [
    { label: "ATS", value: ats ? Math.round(ats.score) : null, weight: ats?.weight ?? null },
    {
      label: "Job match",
      value: hasJobMatch && jobMatch ? Math.round(jobMatch.score) : null,
      weight: hasJobMatch ? (jobMatch?.weight ?? null) : null,
      hint: "Role or JD roast",
    },
    {
      label: "Impact",
      value: impact ? Math.round(impact.score) : null,
      weight: impact?.weight ?? null,
    },
    { label: "Completeness", value: completenessScore, weight: null },
  ];

  return (
    <Card className="mt-5 border-primary/25 bg-gradient-to-b from-primary/[0.05] to-transparent p-5">
      <div className="flex flex-wrap items-center gap-4">
        <span
          className={`font-mono leading-[0.85] font-bold tabular-nums ${band.text} ${
            large ? "text-[96px]" : "text-[72px]"
          }`}
        >
          {score}
        </span>
        <div className="pb-1.5">
          <span className={`${CHIP} ${band.chip}`}>{verdict?.label ?? "Score"}</span>
          <p className="mt-1 text-xs text-muted-foreground">out of 100</p>
        </div>
      </div>
      {verdict && (
        <p className="mt-3 max-w-[72ch] text-sm leading-6 text-muted-foreground">
          {verdict.line}
        </p>
      )}

      <ScoreStrip score={score} />

      <dl className="mt-5 grid grid-cols-2 gap-x-6 gap-y-4 lg:grid-cols-4">
        {metrics.map((metric) => {
          const metricTone = metric.value === null ? null : tone(metric.value);
          return (
            <div key={metric.label}>
              <dt className="flex items-baseline justify-between gap-2 text-xs text-muted-foreground">
                <span>{metric.label}</span>
                {metric.weight !== null && (
                  <span className="font-mono text-[10px]">
                    {Math.round(metric.weight * 100)}%
                  </span>
                )}
              </dt>
              <dd
                className={`mt-1 font-mono text-2xl leading-none font-semibold tabular-nums ${
                  metricTone ? metricTone.text : "text-muted-foreground"
                }`}
              >
                {metric.value ?? "—"}
              </dd>
              <div className="mt-1.5 h-0.5 w-full bg-muted">
                {metric.value !== null && metricTone && (
                  <div
                    className={`h-0.5 ${metricTone.bar}`}
                    style={{ width: `${Math.min(100, Math.max(0, metric.value))}%` }}
                  />
                )}
              </div>
              {metric.value === null && metric.hint && (
                <p className="mt-1 text-[10px] text-muted-foreground">{metric.hint}</p>
              )}
            </div>
          );
        })}
      </dl>

      <div className="mt-5 border-t border-border pt-3">
        <div className="flex items-baseline justify-between gap-3">
          <p className={EYEBROW}>How the score was built</p>
          <p className="font-mono text-[10px] text-muted-foreground">50 / 50</p>
        </div>
        <CompositionBar result={result} />
      </div>
    </Card>
  );
}

function FirstImpressionCard({
  check,
}: {
  check: NonNullable<AnalysisResultPayload["reality_check"]>;
}) {
  return (
    <Card>
      <p className={`${EYEBROW} flex items-center gap-2 text-primary`}>
        <Eye className="size-3.5" aria-hidden />
        Five-second impression
      </p>
      <blockquote className="mt-2 border-l-2 border-primary/60 pl-4">
        <p className="text-[15px] leading-7 italic">{check.five_second_impression}</p>
      </blockquote>
      <p className="mt-2 text-xs leading-5 text-muted-foreground">
        What a recruiter takes away before reading a single bullet.
      </p>
    </Card>
  );
}

function PoisonList({ points }: { points: string[] }) {
  return (
    <Card>
      <p className={`${EYEBROW} flex items-center gap-2 text-destructive`}>
        <AlertTriangle className="size-3.5" aria-hidden />
        Fatal poison points
      </p>
      <ol className="mt-2 sm:columns-2 sm:gap-8">
        {points.map((point, index) => (
          <li
            key={index}
            className="break-inside-avoid border-b border-border py-2 last:border-0"
          >
            <span className="mr-2 font-mono text-[11px] text-destructive">
              {pad(index + 1)}
            </span>
            <span className="text-sm leading-6">{point}</span>
          </li>
        ))}
      </ol>
    </Card>
  );
}

const MARKET_CHIP: Record<MarketVerdict["verdict"], string> = {
  "strong fit": "border-pass/40 text-pass",
  "billable fit with caveats": "border-primary/40 text-primary",
  "borderline / screen fail":
    "border-amber-700/40 text-amber-700 dark:border-yellow-500/40 dark:text-yellow-500",
  "high rejection risk": "border-destructive/40 text-destructive",
};

function MarketCard({ market }: { market: MarketVerdict }) {
  return (
    <Card className="p-4">
      <h3 className="text-sm font-semibold">{market.market}</h3>
      <span className={`${CHIP} mt-2 ${MARKET_CHIP[market.verdict]}`}>
        {market.verdict}
      </span>
      <p className="mt-2 text-xs leading-5 text-muted-foreground">{market.analysis}</p>
      {market.missing_signals.length > 0 && (
        <ul className="mt-2 flex flex-wrap gap-1">
          {market.missing_signals.map((signal) => (
            <li
              key={signal}
              className="rounded border border-border px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground"
            >
              {signal}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

const SEVERITY_CHIP: Record<FixPlanItem["severity"], string> = {
  critical: "border-destructive/40 text-destructive",
  warning:
    "border-amber-700/40 text-amber-700 dark:border-yellow-500/40 dark:text-yellow-500",
  enhancement: "border-primary/40 text-primary",
};

function FixCard({ fix, index }: { fix: FixPlanItem; index: number }) {
  return (
    <Card className="p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="text-sm font-semibold">
          <span className="mr-2 font-mono text-[11px] text-muted-foreground">
            {pad(index + 1)}
          </span>
          {fix.issue}
        </h3>
        <span className={`${CHIP} ${SEVERITY_CHIP[fix.severity]}`}>{fix.severity}</span>
      </div>

      <div className="mt-2 border-l-2 border-destructive/60 pl-3">
        <p className="font-mono text-[10px] tracking-[0.06em] text-destructive uppercase">
          Before
        </p>
        <p className="mt-0.5 text-sm leading-6">{fix.before}</p>
      </div>
      <div className="mt-3 border-l-2 border-pass/60 pl-3">
        <p className="font-mono text-[10px] tracking-[0.06em] text-pass uppercase">
          After
        </p>
        <p className="mt-0.5 text-sm leading-6">{fix.after}</p>
      </div>

      <p className="mt-2 text-xs leading-5 text-muted-foreground">{fix.why}</p>
    </Card>
  );
}

function FindingGroup({
  title,
  items,
  count,
  critical,
  defaultOpen,
}: {
  title: string;
  items: ReportItem[];
  count: number;
  critical?: boolean;
  defaultOpen?: boolean;
}) {
  return (
    <details open={defaultOpen} className="group border-t border-border first:border-t-0">
      <summary className="flex cursor-pointer list-none items-center gap-2 py-3 select-none [&::-webkit-details-marker]:hidden">
        <span className="text-sm font-semibold">{title}</span>
        <span className="font-mono text-[10px] text-muted-foreground">{count}</span>
        <span className="ml-auto font-mono text-[10px] tracking-[0.06em] text-muted-foreground uppercase group-open:hidden">
          Show
        </span>
        <ChevronDown className="size-4 text-muted-foreground transition-transform group-open:rotate-180" />
      </summary>
      <ul className="pb-2 sm:columns-2 sm:gap-8">
        {items.map((item, index) => (
          <li
            key={index}
            className="break-inside-avoid border-t border-border py-2 text-sm leading-6 first:border-t-0"
          >
            <span className={critical ? "text-destructive" : "text-foreground"}>
              {item.text}
            </span>
            <span className="mt-0.5 block font-mono text-[10px] text-muted-foreground">
              {item.source}
            </span>
          </li>
        ))}
      </ul>
    </details>
  );
}

function WorksCard({ notes }: { notes: string[] }) {
  return (
    <Card className="p-4">
      <h3 className="text-sm font-semibold">What works</h3>
      <ul className="mt-2 space-y-1.5">
        {notes.map((note, index) => (
          <li key={index} className="flex gap-2 text-sm leading-6">
            <Check className="mt-1 size-4 shrink-0 text-pass" />
            {note}
          </li>
        ))}
      </ul>
    </Card>
  );
}

function ChecksCard({ result }: { result: AnalysisResultPayload }) {
  const checks = result.breakdown?.deterministic_checks ?? [];
  if (checks.length === 0) return null;

  return (
    <Card className="p-4">
      <h3 className="text-sm font-semibold">Checks</h3>
      <dl className="mt-2 divide-y divide-border">
        {checks.map((check) => (
          <div key={check.name} className="flex items-start justify-between gap-3 py-1.5">
            <dt className="text-xs text-muted-foreground">
              <span className="capitalize">{check.name.replace(/_/g, " ")}</span>
            </dt>
            <dd className="shrink-0 font-mono text-[11px] tabular-nums">
              {check.score}/{check.max}
            </dd>
          </div>
        ))}
      </dl>
    </Card>
  );
}

function VerdictsCard({ summaries }: { summaries: Record<string, string> }) {
  const entries = Object.entries(summaries);
  if (entries.length === 0) return null;

  return (
    <Card className="p-4">
      <h3 className="text-sm font-semibold">Expert verdicts</h3>
      <dl className="mt-2 grid gap-x-8 sm:grid-cols-2">
        {entries.map(([name, summary]) => (
          <div key={name} className="border-t border-border py-2">
            <dt className="font-mono text-[10px] tracking-[0.08em] uppercase text-primary">
              {evaluatorLabel(name)}
            </dt>
            <dd className="mt-0.5 text-xs leading-5">{summary}</dd>
          </div>
        ))}
      </dl>
    </Card>
  );
}

/** The verdict screen: score, headline, first impression, one way forward. */
export function RoastVerdict({
  result,
  verdict,
  analysisType,
  analysisId,
  action,
}: {
  result: AnalysisResultPayload;
  verdict: ScoreVerdict | null;
  analysisType: AnalysisType;
  analysisId: string;
  action?: ReactNode;
}) {
  const check = result.reality_check;
  const roastText = check?.roast ?? result.final_roast;

  return (
    <article>
      <header>
        <div className="flex flex-wrap items-center justify-between gap-3 sm:flex-nowrap">
          <p className={`${EYEBROW} leading-none text-primary`}>
            Roast · {analysisModeLabel(analysisType)}
          </p>
          <div className="flex shrink-0 items-center gap-2">
            <Button asChild size="sm" className="gap-1.5">
              <Link href={`/analysis/${analysisId}/report`}>
                View full report
                <ArrowRight className="size-3.5" />
              </Link>
            </Button>
            {action}
          </div>
        </div>
        <h1 className="mt-2 text-[28px] leading-[1.15] font-bold tracking-tight sm:text-[34px]">
          {check?.headline_verdict ?? "Roast report"}
        </h1>
        {check && (
          <p className="mt-2 max-w-[80ch] text-[15px] leading-7 text-muted-foreground">
            {check.verdict_summary}
          </p>
        )}
      </header>

      <HeroCard result={result} verdict={verdict} large />

      {check?.five_second_impression && (
        <div className="mt-3">
          <FirstImpressionCard check={check} />
        </div>
      )}

      {roastText && (
        <div className="mt-3">
          <Card>
            <p className={`${EYEBROW} flex items-center gap-2 text-primary`}>
              <Flame className="size-3.5" aria-hidden />
              The roast
            </p>
            <div className="mt-3">
              <RoastProse text={roastText} />
            </div>
          </Card>
        </div>
      )}
    </article>
  );
}

/** The full report: every section, one page, behind an explicit click. */
export function RoastReport({
  result,
  verdict,
  analysisType,
  analysisId,
}: {
  result: AnalysisResultPayload;
  verdict: ScoreVerdict | null;
  analysisType: AnalysisType;
  analysisId: string;
}) {
  const check = result.reality_check;
  const score = Math.round(result.overall_score ?? 0);
  const band = tone(score);
  const fixPlan = result.fix_plan;

  const sections: Array<{ title: string; body: ReactNode }> = [];

  if (check && check.poison_points.length > 0) {
    sections.push({
      title: "Fatal poison points",
      body: <PoisonList points={check.poison_points} />,
    });
  }

  if (check && check.market_analysis.length > 0) {
    sections.push({
      title: "Markets",
      body: (
        <div className="grid gap-3 lg:grid-cols-3">
          {check.market_analysis.map((market) => (
            <MarketCard key={market.market} market={market} />
          ))}
        </div>
      ),
    });
  }

  if (fixPlan && fixPlan.fixes.length > 0) {
    sections.push({
      title: "Fix plan",
      body: (
        <div className="grid gap-3 lg:grid-cols-2">
          {fixPlan.fixes.map((fix, index) => (
            <FixCard key={fix.issue} fix={fix} index={index} />
          ))}
        </div>
      ),
    });
  }

  const hasFindings =
    result.critical_issues.length > 0 ||
    result.warnings.length > 0 ||
    result.suggestions.length > 0;
  if (hasFindings) {
    sections.push({
      title: "Findings",
      body: (
        <Card>
          {result.critical_issues.length > 0 && (
            <FindingGroup
              title="Critical issues"
              items={result.critical_issues}
              count={result.critical_issues.length}
              critical
              defaultOpen
            />
          )}
          {result.warnings.length > 0 && (
            <FindingGroup
              title="Warnings"
              items={result.warnings}
              count={result.warnings.length}
            />
          )}
          {result.suggestions.length > 0 && (
            <FindingGroup
              title="Fix these"
              items={result.suggestions}
              count={result.suggestions.length}
            />
          )}
        </Card>
      ),
    });
  }

  const hasEvidence =
    result.positive_notes.length > 0 ||
    (result.breakdown?.deterministic_checks.length ?? 0) > 0 ||
    Object.keys(result.evaluator_summaries).length > 0;
  if (hasEvidence) {
    sections.push({
      title: "Evidence",
      body: (
        <div className="space-y-3">
          <div className="grid gap-3 lg:grid-cols-2">
            {result.positive_notes.length > 0 && (
              <WorksCard notes={result.positive_notes} />
            )}
            <ChecksCard result={result} />
          </div>
          <VerdictsCard summaries={result.evaluator_summaries} />
        </div>
      ),
    });
  }

  return (
    <article>
      <header>
        <div className="flex flex-wrap items-center justify-between gap-3 sm:flex-nowrap">
          <Link
            href={`/analysis/${analysisId}`}
            className="flex items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
          >
            <ArrowLeft className="size-3.5" aria-hidden />
            Back to verdict
          </Link>
          <div className="flex items-center gap-3">
            <span
              className={`font-mono text-xl leading-none font-bold tabular-nums ${band.text}`}
            >
              {score}
            </span>
            <span className={`${CHIP} leading-none ${band.chip}`}>
              {verdict?.label ?? "Score"}
            </span>
            <Button asChild variant="outline" size="sm">
              <Link href="/upload">Roast another</Link>
            </Button>
          </div>
        </div>

        <h1 className="mt-3 text-[24px] leading-tight font-bold tracking-tight sm:text-[28px]">
          {check?.headline_verdict ?? "Roast report"}
        </h1>
        <p className="mt-1 text-xs text-muted-foreground">
          Full report · {analysisModeLabel(analysisType)} · benchmark: senior
          engineering cohort, 2026 market
        </p>
      </header>

      {sections.map((section, index) => (
        <Reveal key={section.title}>
          <SectionLabel
            number={pad(index + 1)}
            title={section.title}
            meta={
              section.title === "Findings" ? <SeverityStrip result={result} /> : undefined
            }
          />
          {section.body}
        </Reveal>
      ))}
    </article>
  );
}
