"use client";

import { motion } from "framer-motion";

function scoreTone(score: number): string {
  if (score >= 70) return "text-primary";
  if (score >= 45) return "text-yellow-500";
  return "text-destructive";
}

/**
 * Animated circular score. The arc sweeps from 0 to `score` on mount and
 * the number sits in the center, colored by band (ember/amber/red).
 */
export function ScoreRing({ score, size = 72 }: { score: number; size?: number }) {
  const clamped = Math.max(0, Math.min(100, score));
  const stroke = Math.max(4, Math.round(size / 14));
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const tone = scoreTone(clamped);

  return (
    <div
      className="relative inline-flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={stroke}
          fill="none"
          className="stroke-muted"
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={stroke}
          stroke="currentColor"
          strokeLinecap="round"
          fill="none"
          className={tone}
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: circumference * (1 - clamped / 100) }}
          transition={{ duration: 1.1, ease: "easeOut" }}
        />
      </svg>
      <span
        className={`absolute font-bold ${tone} ${
          size >= 100 ? "text-4xl" : "text-sm"
        }`}
      >
        {Math.round(clamped)}
      </span>
    </div>
  );
}
