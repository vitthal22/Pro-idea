import type { ReactNode } from "react";

interface StatTileProps {
  icon: ReactNode;
  label: string;
  value: string;
  hint?: string;
}

/** One compact stat tile: label left, value right, optional hint below. */
export function StatTile({ icon, label, value, hint }: StatTileProps) {
  return (
    <div className="h-full rounded-xl border border-border bg-card px-4 py-3">
      <div className="flex items-baseline justify-between gap-3">
        <span className="flex items-center gap-1.5 caption-5 text-muted-foreground">
          {icon}
          {label}
        </span>
        <span className="font-mono text-2xl leading-none font-bold tabular-nums">
          {value}
        </span>
      </div>
      {hint && <p className="mt-1.5 text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}
