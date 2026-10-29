"use client";

import { Loader2 } from "lucide-react";

const STAGES = [
  { key: "extracting", label: "Reading your resume" },
  { key: "parsing", label: "Understanding its structure" },
  { key: "evaluating", label: "Four experts reviewing" },
  { key: "scoring", label: "Calculating your score" },
  { key: "composing", label: "Writing the roast" },
] as const;

/** Live pipeline progress while the roast is being prepared. */
export function StageProgress({ status }: { status: string }) {
  const currentIndex = STAGES.findIndex((stage) => stage.key === status);

  return (
    <div className="mx-auto max-w-md rounded-2xl border border-border bg-card p-8 text-center">
      <Loader2 className="mx-auto size-8 animate-spin text-primary" />
      <h2 className="mt-4 text-xl font-semibold">Cooking your roast…</h2>
      <p className="mt-2 text-muted-foreground">
        Four experts are reading your resume. This usually takes one to three
        minutes — you can leave this page, your roast will be waiting.
      </p>
      <ol className="mt-6 space-y-2 text-left">
        {STAGES.map((stage, index) => {
          const done = currentIndex > index;
          const active = currentIndex === index;
          return (
            <li
              key={stage.key}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm ${
                active
                  ? "bg-primary/10 font-medium text-primary"
                  : done
                    ? "text-muted-foreground"
                    : "text-muted-foreground/50"
              }`}
            >
              <span
                className={`size-2 rounded-full ${
                  done
                    ? "bg-primary"
                    : active
                      ? "bg-primary animate-pulse"
                      : "bg-muted-foreground/30"
                }`}
              />
              {stage.label}
              {done && <span className="ml-auto text-xs">done</span>}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
