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
  QUEUED: "secondary",
  EXTRACTING: "secondary",
  PARSING: "secondary",
  EVALUATING: "default",
  SCORING: "default",
  COMPOSING: "default",
  COMPLETE: "default",
  PARTIAL: "outline",
  FAILED: "destructive",
};

const MODE_LABELS: Record<AnalysisListItem["analysis_type"], string> = {
  general: "General",
  role_based: "Role-based",
  jd_based: "JD-based",
  custom: "Custom",
};

export function AnalysisCard({ analysis }: { analysis: AnalysisListItem }) {
  const created = new Date(analysis.created_at).toLocaleString();

  return (
    <Link href={`/analysis/${analysis.id}`} className="block">
      <Card className="transition-colors hover:border-primary/50">
        <CardHeader>
          <div className="flex items-center justify-between gap-2">
            <CardTitle className="text-base">
              {MODE_LABELS[analysis.analysis_type]} analysis
            </CardTitle>
            <Badge variant={STATUS_VARIANTS[analysis.status]}>
              {analysis.status}
            </Badge>
          </div>
          <CardDescription>Created {created}</CardDescription>
        </CardHeader>
      </Card>
    </Link>
  );
}
