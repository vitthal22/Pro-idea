"use client";

import { motion } from "framer-motion";
import Link from "next/link";

import { ScoreRing } from "@/components/analysis/score-ring";
import { StatusBadge } from "@/components/shared/status-badge";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { formatDate } from "@/lib/format";
import { analysisModeLabel } from "@/lib/analysis-modes";
import { isRunningStatus, type AnalysisListItem } from "@/types/analysis";

export function AnalysisCard({ analysis }: { analysis: AnalysisListItem }) {
  const created = formatDate(analysis.created_at);
  const running = isRunningStatus(analysis.status);

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
                  {analysisModeLabel(analysis.analysis_type)} analysis
                </CardTitle>
                <CardDescription>
                  {running ? "Roasting now — tap to watch live" : `Created ${created}`}
                </CardDescription>
              </div>
              <StatusBadge status={analysis.status} />
            </div>
          </CardHeader>
        </Card>
      </Link>
    </motion.div>
  );
}
