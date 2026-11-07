"use client";

import { Flame, History, LayoutDashboard, LogOut, Plus, User } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { SidebarToggle } from "@/components/layout/sidebar-toggle";
import { Button } from "@/components/ui/button";
import { useLogout } from "@/hooks/queries/use-auth";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/history", label: "Roasts", icon: History },
  { href: "/analytics", label: "Analytics", icon: ChartIcon },
];

const COLLAPSED_LABEL = "group-data-[collapsed=true]/sidebar:sr-only";

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
    <Link
      href="/dashboard"
      aria-label="Resume Roaster"
      className="flex items-center gap-3 px-2 py-1 group-data-[collapsed=true]/sidebar:justify-center group-data-[collapsed=true]/sidebar:px-0"
    >
      <span className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-primary/15 text-primary">
        <Flame className="size-5" />
      </span>
      <span className={COLLAPSED_LABEL}>
        <span className="block font-heading text-sm leading-tight font-semibold">
          Resume Roaster
        </span>
        <span className="block text-xs text-muted-foreground">
          Get roasted. Get better.
        </span>
      </span>
    </Link>
  );
}

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <nav aria-label="Main" className="grid gap-1">
      {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
        const active = pathname === href || pathname.startsWith(`${href}/`);
        return (
          <Link
            key={href}
            href={href}
            onClick={onNavigate}
            aria-current={active ? "page" : undefined}
            title={label}
            className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors group-data-[collapsed=true]/sidebar:justify-center group-data-[collapsed=true]/sidebar:px-0 ${
              active
                ? "bg-primary/12 font-medium text-primary"
                : "text-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
            }`}
          >
            <Icon className="size-4 shrink-0" />
            <span className={COLLAPSED_LABEL}>{label}</span>
          </Link>
        );
      })}
    </nav>
  );
}

/**
 * The sidebar's shared content — rendered in the desktop rail and in the
 * mobile Sheet. `onNavigate` closes the Sheet after a tap.
 */
export function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const router = useRouter();
  const pathname = usePathname();
  const logout = useLogout();

  function handleLogout() {
    logout.mutate(undefined, {
      onSettled: () => router.replace("/"),
    });
  }

  return (
    <div className="flex h-full flex-col gap-3 p-3">
      <Brand />

      <NavLinks onNavigate={onNavigate} />

      <Button
        asChild
        className="justify-start gap-2 group-data-[collapsed=true]/sidebar:justify-center group-data-[collapsed=true]/sidebar:px-0"
        variant="default"
      >
        <Link href="/upload" onClick={onNavigate} title="New roast">
          <Plus className="size-4 shrink-0" />
          <span className={COLLAPSED_LABEL}>New roast</span>
        </Link>
      </Button>

      {/* Utilities: the collapse control, then Profile and Log out. The
          light/dark switch deliberately lives on the Profile page instead. */}
      <div className="mt-auto space-y-2 border-t border-sidebar-border pt-3">
        <SidebarToggle />

        <div className="flex items-center justify-between gap-2 px-1 group-data-[collapsed=true]/sidebar:flex-col group-data-[collapsed=true]/sidebar:items-center group-data-[collapsed=true]/sidebar:gap-1">
          <Link
            href="/profile"
            onClick={onNavigate}
            aria-current={pathname === "/profile" ? "page" : undefined}
            title="Profile"
            className="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground group-data-[collapsed=true]/sidebar:size-8 group-data-[collapsed=true]/sidebar:justify-center group-data-[collapsed=true]/sidebar:px-0"
          >
            <User className="size-4 shrink-0" />
            <span className={COLLAPSED_LABEL}>Profile</span>
          </Link>

          <Button
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            disabled={logout.isPending}
            title="Log out"
            className="text-muted-foreground group-data-[collapsed=true]/sidebar:size-7 group-data-[collapsed=true]/sidebar:px-0"
          >
            <LogOut className="size-4" />
            <span className={COLLAPSED_LABEL}>Log out</span>
          </Button>
        </div>
      </div>
    </div>
  );
}
