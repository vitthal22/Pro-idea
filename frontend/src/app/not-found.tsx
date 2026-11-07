import type { Metadata } from "next";
import Link from "next/link";

import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "Page not found — Resume Roaster",
};

export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-[60vh] w-full max-w-2xl flex-col items-center justify-center px-4 py-12 text-center">
      <span className="rounded-md border border-border bg-card px-3 py-1 font-mono text-xs tracking-widest text-primary">
        404
      </span>
      <h1 className="mt-4 heading-4 text-balance">
        This page was not invited to the interview.
      </h1>
      <p className="mt-2 max-w-md body-6 text-muted-foreground">
        The link is broken, the page moved, or this route never made it past
        the screening round.
      </p>
      <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
        <Button asChild>
          <Link href="/">Back to the roast</Link>
        </Button>
        <Button variant="ghost" asChild>
          <Link href="/dashboard">Open dashboard</Link>
        </Button>
      </div>
    </main>
  );
}
