"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type {
  AnalysisListItem,
  AnalysisStatusResponse,
} from "@/types/analysis";

/** List the current user's analyses. */
export function useAnalyses() {
  return useQuery({
    queryKey: ["analyses"],
    queryFn: () => apiFetch<AnalysisListItem[]>("/api/v1/analyses"),
  });
}

/** Fetch a single analysis (status + metadata). */
export function useAnalysis(id: string | null) {
  return useQuery({
    queryKey: ["analyses", id],
    queryFn: () =>
      apiFetch<AnalysisStatusResponse>(`/api/v1/analyses/${id}/status`),
    enabled: Boolean(id),
  });
}
