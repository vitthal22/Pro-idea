"use client";

import { useMutation } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type { AnalysisCreatedResponse, AnalysisType } from "@/types/analysis";

export interface StartAnalysisInput {
  resumeId: string;
  analysisType?: AnalysisType;
  targetRole?: string;
  jobDescription?: string;
  customInstructions?: string;
}

/** Start a roast for a resume; the pipeline runs on the server. */
export function useStartAnalysis() {
  return useMutation({
    mutationFn: async (input: StartAnalysisInput) =>
      apiFetch<AnalysisCreatedResponse>("/api/v1/analyses", {
        method: "POST",
        body: JSON.stringify({
          resume_id: input.resumeId,
          analysis_type: input.analysisType ?? "general",
          target_role: input.targetRole || null,
          job_description: input.jobDescription || null,
          custom_instructions: input.customInstructions || null,
        }),
      }),
  });
}
