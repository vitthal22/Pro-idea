"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type { ResumeListResponse } from "@/types/resume";

/** List the current user's resumes (newest first). */
export function useResumes() {
  return useQuery({
    queryKey: ["resumes"],
    queryFn: () => apiFetch<ResumeListResponse>("/api/v1/resumes"),
  });
}
