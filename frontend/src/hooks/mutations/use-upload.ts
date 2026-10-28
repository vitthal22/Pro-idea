"use client";

import { useMutation } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type { ResumeResponse } from "@/types/resume";

/** Upload a resume file; resolves with the created resume record. */
export function useUploadResume() {
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      // Never set Content-Type manually — the browser must add the
      // multipart boundary (forcing JSON here breaks the upload with 422).
      formData.append("file", file);
      return apiFetch<ResumeResponse>("/api/v1/resumes/upload", {
        method: "POST",
        body: formData,
      });
    },
  });
}
