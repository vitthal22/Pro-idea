"use client";

import { motion } from "framer-motion";
import Link from "next/link";

import { ScoreRing } from "@/components/analysis/score-ring";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { AnalysisListItem, AnalysisStatus } from "@/types/analysis";

const STATUS_VARIANTS: Record<
  AnalysisStatus,
  "default" | "secondary" | "destructive" | "outline"
> = {
  queued: "secondary",
  extracting: "secondary",
  parsing: "secondary",
  evaluating: "secondary",
  scoring: "secondary",
  composing: "secondary",
  completed: "default",
  partial: "outline",
  failed: "destructive",
};

const MODE_LABELS: Record<AnalysisListItem["analysis_type"], string> = {
  general: "General",
  role_based: "Role-based",
  jd_based: "JD-based",
  custom: "Custom",
};

export function AnalysisCard({ analysis }: { analysis: AnalysisListItem }) {
  const created = new Date(analysis.created_at).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });

  return (
    <motion.div whileHover={{ y: -2 }} transition={{ duration: 0.15 }}>
      <Link href={`/analysis/${analysis.id}`} className="block">
        <Card className="transition-colors hover:border-primary/50">
          <CardHeader>
            <div className="flex items-center gap-4">
              {analysis.overall_score !== null ? (
                <ScoreRing score={analysis.overall_score} size={52} />
              ) : (
                <span
                  className="size-11 shrink-0 rounded-full border-2 border-dashed border-border"
                  aria-hidden
                />
              )}
              <div className="min-w-0 flex-1">
                <CardTitle className="text-base">
                  {MODE_LABELS[analysis.analysis_type]} analysis
                </CardTitle>
                <CardDescription>Created {created}</CardDescription>
              </div>
              <Badge variant={STATUS_VARIANTS[analysis.status]}>
                {analysis.status}
              </Badge>
            </div>
          </CardHeader>
        </Card>
      </Link>
    </motion.div>
  );
}
