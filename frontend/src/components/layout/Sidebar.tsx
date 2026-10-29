"use client";

import { Flame, History, LayoutDashboard, LogOut, Plus, User } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { useLogout } from "@/hooks/queries/use-auth";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/history", label: "Roasts", icon: History },
  { href: "/analytics", label: "Analytics", icon: ChartIcon },
];

function ChartIcon({ className }: { className?: string }) {
  // Small inline bars — lucide's chart icon set churns between versions,
  // so the nav draws its own to stay stable.
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      className={className}
      aria-hidden
    >
      <path d="M6 20v-6" />
      <path d="M12 20V8" />
      <path d="M18 20v-9" />
    </svg>
  );
}

function Brand() {
  return (
    <Link href="/dashboard" className="flex items-center gap-3 px-2 py-1">
      <span className="flex size-9 items-center justify-center rounded-xl bg-primary/15 text-primary">
        <Flame className="size-5" />
      </span>
      <span>
        <span className="block font-semibold leading-tight">Resume Roaster</span>
        <span className="block text-xs text-muted-foreground">Get roasted. Get better.</span>
      </span>
    </Link>
  );
}

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <nav className="grid gap-1 px-2">
      {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
        const active = pathname === href || pathname.startsWith(`${href}/`);
        return (
          <Link
            key={href}
            href={href}
            onClick={onNavigate}
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
              active
                ? "bg-primary/12 font-medium text-primary"
                : "text-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
            }`}
          >
            <Icon className="size-4" />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}

/**
 * The sidebar's shared content — rendered in the desktop column and in the
 * mobile Sheet. `onNavigate` closes the Sheet after a tap.
 */
export function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const router = useRouter();
  const logout = useLogout();

  function handleLogout() {
    logout.mutate(undefined, {
      onSettled: () => router.replace("/"),
    });
  }

  return (
    <div className="flex h-full flex-col gap-6 p-4">
      <Brand />

      <NavLinks onNavigate={onNavigate} />

      <Button asChild className="mx-2 justify-start gap-2" variant="default">
        <Link href="/upload" onClick={onNavigate}>
          <Plus className="size-4" />
          New roast
        </Link>
      </Button>

      <nav className="grid gap-1 px-2">
        <Link
          href="/profile"
          onClick={onNavigate}
          className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
        >
          <User className="size-4" />
          Profile
        </Link>
      </nav>

      <div className="mt-auto flex items-center justify-between border-t border-sidebar-border pt-4 px-2">
        <ThemeToggle />
        <Button
          variant="ghost"
          size="sm"
          onClick={handleLogout}
          disabled={logout.isPending}
          className="text-muted-foreground"
        >
          <LogOut className="size-4" />
          Log out
        </Button>
      </div>
    </div>
  );
}
