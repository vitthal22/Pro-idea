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
