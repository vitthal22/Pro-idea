"use client";

import Link from "next/link";

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
    <Link href={`/analysis/${analysis.id}`} className="block">
      <Card className="transition-colors hover:border-primary/50">
        <CardHeader>
          <div className="flex items-center justify-between gap-2">
            <CardTitle className="text-base">
              {MODE_LABELS[analysis.analysis_type]} analysis
            </CardTitle>
            <div className="flex items-center gap-2">
              {analysis.overall_score !== null && (
                <span className="text-sm font-semibold">
                  {Math.round(analysis.overall_score)}/100
                </span>
              )}
              <Badge variant={STATUS_VARIANTS[analysis.status]}>
                {analysis.status}
              </Badge>
            </div>
          </div>
          <CardDescription>Created {created}</CardDescription>
        </CardHeader>
      </Card>
    </Link>
  );
}
