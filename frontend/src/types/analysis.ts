/** TypeScript mirrors of backend analysis schemas (app/api/schemas/analyses.py). */

export type AnalysisType = "general" | "role_based" | "jd_based" | "custom";

export type AnalysisStatus =
  | "QUEUED"
  | "EXTRACTING"
  | "PARSING"
  | "EVALUATING"
  | "SCORING"
  | "COMPOSING"
  | "COMPLETE"
  | "PARTIAL"
  | "FAILED";

export interface AnalysisListItem {
  id: string;
  resume_id: string;
  analysis_type: AnalysisType;
  status: AnalysisStatus;
  created_at: string;
}

export interface AnalysisStatusResponse {
  id: string;
  status: AnalysisStatus;
  error_message: string | null;
}
