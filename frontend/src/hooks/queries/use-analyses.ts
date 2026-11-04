"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import {
  isRunningStatus,
  type AnalysisDetail,
  type AnalysisListResponse,
} from "@/types/analysis";

interface AnalysesParams {
  limit?: number;
  offset?: number;
}

/** List the current user's analyses (roasts), newest first. */
export function useAnalyses({ limit, offset }: AnalysesParams = {}) {
  const query = new URLSearchParams();
  if (limit !== undefined) query.set("limit", String(limit));
  if (offset !== undefined) query.set("offset", String(offset));
  const suffix = query.size > 0 ? `?${query.toString()}` : "";

  return useQuery({
    queryKey: ["analyses", limit ?? "default", offset ?? 0],
    queryFn: () => apiFetch<AnalysisListResponse>(`/api/v1/analyses${suffix}`),
  });
}

/**
 * One analysis. While the pipeline runs, refetches every 2 seconds so the
 * result page shows live progress; stops polling at a terminal status.
 * Pass `{ poll: false }` when the SSE stream drives updates instead.
 */
export function useAnalysis(
  id: string,
  options?: { poll?: boolean },
) {
  const poll = options?.poll ?? true;
  return useQuery({
    queryKey: ["analyses", id],
    queryFn: () => apiFetch<AnalysisDetail>(`/api/v1/analyses/${id}`),
    refetchInterval: (query) => {
      if (!poll) return false;
      const status = query.state.data?.status;
      return status && isRunningStatus(status) ? 2000 : false;
    },
  });
}
