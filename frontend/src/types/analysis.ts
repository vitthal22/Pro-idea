/** TypeScript mirrors of backend analysis schemas (app/api/schemas/analyses.py). */

export type AnalysisType = "general" | "role_based" | "jd_based" | "custom";

/** Matches the backend status flow exactly (lowercase). */
export type AnalysisStatus =
  | "queued"
  | "extracting"
  | "parsing"
  | "evaluating"
  | "scoring"
  | "composing"
  | "completed"
  | "partial"
  | "failed";

/** Stages the pipeline walks through before a terminal state. */
export const RUNNING_STATUSES: ReadonlySet<AnalysisStatus> = new Set([
  "queued",
  "extracting",
  "parsing",
  "evaluating",
  "scoring",
  "composing",
]);

export function isRunningStatus(status: AnalysisStatus): boolean {
  return RUNNING_STATUSES.has(status);
}

export interface ReportItem {
  text: string;
  source: string;
}

export interface DeterministicCheck {
  name: string;
  score: number;
  max: number;
  details: string;
}

export interface CategoryScore {
  category: string;
  rating: string;
  score: number;
  weight: number;
  details: string;
}

export interface ScoringBreakdown {
  deterministic_checks: DeterministicCheck[];
  deterministic_score: number;
  ai_categories: CategoryScore[];
  ai_score: number;
}

/** Job Matcher output — only present for role_based/jd_based analyses. */
export interface JobMatchFeedback {
  summary: string;
  match_rating: string;
  matched_skills: string[];
  missing_skills: string[];
  alignment_findings: string[];
  recommendations: string[];
}

/** One hiring-market verdict from the 2026 Hiring Panel composer. */
export interface MarketVerdict {
  market: "Product Tech & Tier-1" | "Service & Consulting" | "2026 AI-Era Market";
  verdict:
    | "strong fit"
    | "billable fit with caveats"
    | "borderline / screen fail"
    | "high rejection risk";
  analysis: string;
  missing_signals: string[];
}

/** Structured "Unfiltered Recruiter Reality Check" (composer v2). */
export interface RealityCheck {
  headline_verdict: string;
  verdict_summary: string;
  five_second_impression: string;
  poison_points: string[];
  market_analysis: MarketVerdict[];
  roast: string;
}

/** Blunt score verdict shown on the scorecard. */
export interface ScoreVerdict {
  label: string;
  line: string;
}

/** The roast itself — mirrors backend AnalysisResultPayload. */
export interface AnalysisResultPayload {
  overall_score: number | null;
  critical_issues: ReportItem[];
  warnings: ReportItem[];
  suggestions: ReportItem[];
  positive_notes: string[];
  final_roast: string | null;
  breakdown: ScoringBreakdown | null;
  methodology: Record<string, unknown> | null;
  job_match_feedback: JobMatchFeedback | null;
  reality_check: RealityCheck | null;
  evaluator_summaries: Record<string, string>;
  failed_evaluators: string[];
  roast_fallback_used: boolean;
}

/** Full analysis record — mirrors backend AnalysisDetailResponse. */
export interface AnalysisDetail {
  id: string;
  resume_id: string;
  analysis_type: AnalysisType;
  status: AnalysisStatus;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
  processing_time_ms: number | null;
  score_verdict: ScoreVerdict | null;
  result: AnalysisResultPayload | null;
}

export interface AnalysisStatusResponse {
  id: string;
  status: AnalysisStatus;
  error_message: string | null;
}

export interface AnalysisListItem {
  id: string;
  resume_id: string;
  analysis_type: AnalysisType;
  status: AnalysisStatus;
  created_at: string;
  overall_score: number | null;
}

export interface AnalysisListResponse {
  items: AnalysisListItem[];
  total: number;
}

/** POST /api/v1/analyses acknowledgement (202). */
export interface AnalysisCreatedResponse {
  analysis_id: string;
  status: string;
}
