"use client";

import { Flame } from "lucide-react";
import Link from "next/link";

import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { useCurrentUser } from "@/hooks/queries/use-auth";

const SECTIONS = [
  { href: "#features", label: "Features" },
  { href: "#how-it-works", label: "How it works" },
  { href: "#faq", label: "Questions" },
];

/**
 * A compact bar that floats off the top edge instead of sitting flush against
 * it: translucent surface, blurred page behind, sized to its content.
 */
export function LandingNavbar() {
  const { data: user } = useCurrentUser();

  return (
    <header className="sticky top-3 z-40 mx-auto w-fit max-w-[calc(100vw-1.5rem)] rounded-full border border-border bg-card/70 shadow-lg backdrop-blur-xl">
      <div className="flex items-center gap-1 px-2 py-2 sm:gap-2 sm:px-3">
        <Link
          href="/"
          className="flex items-center gap-2 rounded-full px-2 py-1 font-heading text-sm font-semibold tracking-tight transition-colors hover:text-primary"
        >
          <span className="flex size-7 items-center justify-center rounded-lg bg-primary/15 text-primary">
            <Flame className="size-4" aria-hidden />
          </span>
          Resume Roaster
        </Link>

        <nav aria-label="Sections" className="hidden items-center gap-1 md:flex">
          {SECTIONS.map((section) => (
            <Link
              key={section.href}
              href={section.href}
              className="rounded-full px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              {section.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-1 sm:gap-2">
          <ThemeToggle />
          {user ? (
            <Button asChild size="sm">
              <Link href="/dashboard">Open dashboard</Link>
            </Button>
          ) : (
            <>
              <Button
                variant="ghost"
                size="sm"
                className="hidden sm:inline-flex"
                asChild
              >
                <Link href="/login">Log in</Link>
              </Button>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/register">Get started</Link>
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
