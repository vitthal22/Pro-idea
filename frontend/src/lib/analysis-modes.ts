/** Analysis modes and the role catalog shared by the upload flow. */

export const ANALYSIS_MODES = [
  {
    value: "general",
    label: "General",
    hint: "The full four-expert roast, no target.",
  },
  {
    value: "role_based",
    label: "Role-based",
    hint: "Judged against a specific role.",
  },
  {
    value: "jd_based",
    label: "JD-based",
    hint: "Matched against a job posting.",
  },
  {
    value: "custom",
    label: "Custom",
    hint: "You choose what gets roasted hardest.",
  },
] as const;

export type AnalysisModeValue = (typeof ANALYSIS_MODES)[number]["value"];

export const ROLE_OPTIONS = [
  { value: "frontend_dev", label: "Frontend Developer" },
  { value: "backend_dev", label: "Backend Developer" },
  { value: "fullstack_dev", label: "Fullstack Developer" },
  { value: "ai_engineer", label: "AI Engineer" },
  { value: "data_scientist", label: "Data Scientist" },
  { value: "devops", label: "DevOps / SRE" },
  { value: "software_engineer", label: "Software Engineer" },
  { value: "product_manager", label: "Product Manager" },
] as const;

export const JD_MAX_CHARS = 5000;
export const CUSTOM_INSTRUCTIONS_MAX_CHARS = 500;
