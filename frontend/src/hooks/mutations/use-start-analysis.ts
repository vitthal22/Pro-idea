"use client";

import { useMutation } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type { AnalysisCreatedResponse } from "@/types/analysis";

/** Start a roast for a resume; the pipeline runs on the server. */
export function useStartAnalysis() {
  return useMutation({
    mutationFn: async (input: { resumeId: string; analysisType?: string }) =>
      apiFetch<AnalysisCreatedResponse>("/api/v1/analyses", {
        method: "POST",
        body: JSON.stringify({
          resume_id: input.resumeId,
          analysis_type: input.analysisType ?? "general",
        }),
      }),
  });
}
