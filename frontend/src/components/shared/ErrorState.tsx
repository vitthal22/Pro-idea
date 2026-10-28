"use client";

import { RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";

interface ErrorStateProps {
  title: string;
  description?: string;
  onRetry: () => void;
}

/** Shared "something failed" panel with a retry action. */
export function ErrorState({ title, description, onRetry }: ErrorStateProps) {
  return (
    <div className="mx-auto max-w-md rounded-2xl border border-border bg-card p-6 text-center">
      <p className="font-medium text-destructive">{title}</p>
      {description && (
        <p className="mt-2 text-muted-foreground">{description}</p>
      )}
      <Button variant="outline" onClick={onRetry} className="mt-4">
        <RefreshCw className="size-4" />
        Retry
      </Button>
    </div>
  );
}
