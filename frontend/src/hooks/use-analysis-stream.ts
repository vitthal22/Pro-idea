"use client";

import { useEffect, useRef } from "react";

import { API_BASE_URL } from "@/lib/api-client";
import { useAuthStore } from "@/stores/auth-store";
import type { AnalysisStatus } from "@/types/analysis";

export type AnalysisStreamEvent =
  | { kind: "status"; step: AnalysisStatus }
  | { kind: "complete"; overallScore: number | null }
  | { kind: "failed"; message: string };

interface UseAnalysisStreamOptions {
  id: string;
  enabled: boolean;
  onEvent: (event: AnalysisStreamEvent) => void;
  onError: () => void;
}

/**
 * Consume `GET /analyses/{id}/stream` (SSE) over fetch — EventSource cannot
 * send the Authorization header, so the stream is parsed by hand. Any error
 * (network, auth expiry, parse) fires `onError` once and the caller falls
 * back to status polling.
 */
export function useAnalysisStream({
  id,
  enabled,
  onEvent,
  onError,
}: UseAnalysisStreamOptions): void {
  // Latest-callback refs keep the effect dependent only on [id, enabled].
  const onEventRef = useRef(onEvent);
  const onErrorRef = useRef(onError);
  onEventRef.current = onEvent;
  onErrorRef.current = onError;

  useEffect(() => {
    if (!enabled) return;

    const controller = new AbortController();
    let cancelled = false;

    async function consume() {
      const token = useAuthStore.getState().token;
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/v1/analyses/${id}/stream`,
          {
            headers: token ? { Authorization: `Bearer ${token}` } : undefined,
            credentials: "include",
            signal: controller.signal,
          },
        );
        if (!response.ok || !response.body) {
          onErrorRef.current();
          return;
        }
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        for (;;) {
          const { done, value } = await reader.read();
          if (done || cancelled) break;
          buffer += decoder.decode(value, { stream: true });
          const frames = buffer.split("\n\n");
          buffer = frames.pop() ?? "";
          for (const frame of frames) {
            const eventLine = frame
              .split("\n")
              .find((line) => line.startsWith("event: "));
            const dataLine = frame
              .split("\n")
              .find((line) => line.startsWith("data: "));
            if (!eventLine || !dataLine) continue; // heartbeat comment
            const event = eventLine.slice("event: ".length);
            const data = JSON.parse(dataLine.slice("data: ".length)) as {
              step?: AnalysisStatus;
              overall_score?: number | null;
              message?: string;
            };
            if (event === "status" && data.step) {
              onEventRef.current({ kind: "status", step: data.step });
            } else if (event === "complete") {
              onEventRef.current({
                kind: "complete",
                overallScore: data.overall_score ?? null,
              });
            } else if (event === "error") {
              onEventRef.current({
                kind: "failed",
                message: data.message ?? "The pipeline failed.",
              });
            }
          }
        }
      } catch (error) {
        if (!cancelled && (error as Error).name !== "AbortError") {
          onErrorRef.current();
        }
      }
    }

    void consume();
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [id, enabled]);
}
