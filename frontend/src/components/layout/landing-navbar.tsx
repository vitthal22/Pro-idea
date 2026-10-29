"use client";

import { Flame } from "lucide-react";
import Link from "next/link";

import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { useCurrentUser } from "@/hooks/queries/use-auth";

/** Sticky glass navbar for public pages. */
export function LandingNavbar() {
  const { data: user } = useCurrentUser();

  return (
    <header className="glass-card sticky top-0 z-40 border-x-0 border-t-0">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2.5 font-semibold">
          <span className="flex size-8 items-center justify-center rounded-lg bg-primary/15 text-primary">
            <Flame className="size-4.5" />
          </span>
          Resume Roaster
        </Link>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          {user ? (
            <Button asChild>
              <Link href="/dashboard">Open dashboard</Link>
            </Button>
          ) : (
            <>
              <Button variant="ghost" asChild>
                <Link href="/login">Log in</Link>
              </Button>
              <Button asChild>
                <Link href="/register">Get started</Link>
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
