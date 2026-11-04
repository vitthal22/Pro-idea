"use client";

import { Menu } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { SidebarContent } from "@/components/layout/Sidebar";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { useMounted } from "@/hooks/use-mounted";
import { useAuthStore } from "@/stores/auth-store";
import { useUiStore } from "@/stores/ui-store";

/**
 * Shell for every logged-in page: one auth guard, one layout. The sidebar is a
 * sticky column on desktop — collapsible to a 72px icon rail — and a Sheet
 * behind a hamburger below the lg breakpoint.
 */
export default function AppLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const mounted = useMounted();
  const token = useAuthStore((s) => s.token);
  const collapsed = useUiStore((s) => s.collapsed);
  const [navOpen, setNavOpen] = useState(false);
  // Enabled one frame after mount so restoring a collapsed sidebar does not
  // animate the width on every hard page load.
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const frame = requestAnimationFrame(() => setReady(true));
    return () => cancelAnimationFrame(frame);
  }, []);

  // The stored preference only exists on the client. Render expanded until
  // mount so the server HTML and the first client paint agree.
  const sidebarCollapsed = mounted && collapsed;

  useEffect(() => {
    if (mounted && !token) {
      router.replace("/login");
    }
  }, [mounted, token, router]);

  return (
    <div className="flex min-h-screen bg-background">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:rounded-md focus:border focus:border-border focus:bg-card focus:px-3 focus:py-2 focus:text-sm focus:text-foreground"
      >
        Skip to content
      </a>

      <aside
        id="app-sidebar"
        data-collapsed={sidebarCollapsed}
        className={`group/sidebar sticky top-0 hidden h-svh shrink-0 flex-col overflow-x-clip overflow-y-auto border-r border-sidebar-border bg-sidebar lg:flex ${
          sidebarCollapsed ? "w-[4.5rem]" : "w-64"
        } ${
          ready
            ? "transition-[width] duration-150 ease-out motion-reduce:transition-none"
            : ""
        }`}
      >
        <SidebarContent />
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-border px-4 py-2.5 lg:hidden">
          <Sheet open={navOpen} onOpenChange={setNavOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" aria-label="Open menu">
                <Menu className="size-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-72 p-0">
              <SheetTitle className="sr-only">Navigation</SheetTitle>
              <SidebarContent onNavigate={() => setNavOpen(false)} />
            </SheetContent>
          </Sheet>
          <Link href="/dashboard" className="font-semibold">
            Resume Roaster
          </Link>
          <span className="size-8" aria-hidden />
        </header>

        {/* One constant outer frame for every page. Pages narrow their own
            content (prose / form) instead of moving the outer edge. */}
        <main
          id="main-content"
          tabIndex={-1}
          className="mx-auto w-full max-w-6xl flex-1 px-4 py-4 outline-none md:px-8 md:py-5"
        >
          {/* Without a token the page must not mount: otherwise its queries
              fire unauthenticated while the redirect is in flight (two 401s
              per logged-out visit). */}
          {token ? children : null}
        </main>
      </div>
    </div>
  );
}
