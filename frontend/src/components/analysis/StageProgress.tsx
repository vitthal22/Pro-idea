"use client";

import { motion } from "framer-motion";
import { Check, Flame, Loader2 } from "lucide-react";

const STAGES = [
  { key: "extracting", label: "Reading your resume" },
  { key: "parsing", label: "Understanding its structure" },
  { key: "evaluating", label: "Four experts reviewing" },
  { key: "scoring", label: "Calculating your score" },
  { key: "composing", label: "Writing the roast" },
] as const;

// Queued sits before the first stage; each stage adds its share of the bar.
const STAGE_PROGRESS: Record<string, number> = {
  queued: 4,
  extracting: 16,
  parsing: 36,
  evaluating: 60,
  scoring: 80,
  composing: 94,
};

/** The roast experience: animated flame, ember progress bar, live stages. */
export function StageProgress({ status }: { status: string }) {
  const currentIndex = STAGES.findIndex((stage) => stage.key === status);
  const progress = STAGE_PROGRESS[status] ?? 10;

  return (
    <div className="relative mx-auto max-w-md">
      {/* Pulsing ember glow behind the card */}
      <div
        className="bg-glow-ember pointer-events-none absolute -inset-6 animate-pulse"
        aria-hidden
      />
      <div className="relative rounded-2xl border border-primary/25 bg-card p-8 text-center">
        <motion.span
          className="mx-auto flex size-16 items-center justify-center rounded-2xl bg-primary/15 text-primary"
          animate={{ scale: [1, 1.1, 1] }}
          transition={{ repeat: Infinity, duration: 1.6, ease: "easeInOut" }}
        >
          <Flame className="size-8" />
        </motion.span>

        <h2 className="mt-4 text-xl font-semibold">Cooking your roast…</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Four experts are reading your resume. This usually takes one to
          three minutes — you can leave this page, your roast will be waiting.
        </p>

        <div className="mt-6 h-2 overflow-hidden rounded-full bg-muted">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-primary to-amber-500"
            initial={{ width: "4%" }}
            animate={{ width: `${progress}%` }}
            transition={{ type: "spring", stiffness: 60, damping: 20 }}
          />
        </div>

        <ol className="mt-6 space-y-2 text-left">
          {STAGES.map((stage, index) => {
            const done = currentIndex > index;
            const active = currentIndex === index;
            return (
              <li
                key={stage.key}
                className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                  active
                    ? "bg-primary/10 font-medium text-primary"
                    : done
                      ? "text-muted-foreground"
                      : "text-muted-foreground/50"
                }`}
              >
                {done ? (
                  <span className="flex size-5 items-center justify-center rounded-full bg-primary text-primary-foreground">
                    <Check className="size-3" />
                  </span>
                ) : active ? (
                  <Loader2 className="size-5 shrink-0 animate-spin text-primary" />
                ) : (
                  <span className="ml-1 size-3 rounded-full bg-muted-foreground/30" />
                )}
                {stage.label}
                {done && <span className="ml-auto text-xs">done</span>}
              </li>
            );
          })}
        </ol>
      </div>
    </div>
  );
}
