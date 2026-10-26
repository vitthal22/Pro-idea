"use client";

import { ClipboardList, LogOut, Upload } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { useMounted } from "@/hooks/use-mounted";
import { useCurrentUser, useLogout } from "@/hooks/queries/use-auth";
import { useAuthStore } from "@/stores/auth-store";

const NAV_ITEMS = [
  { href: "/dashboard", label: "History", icon: ClipboardList },
  { href: "/upload", label: "Upload", icon: Upload },
];

function SidebarNav() {
  const pathname = usePathname();
  return (
    <nav className="grid gap-1">
      {NAV_ITEMS.map(({ href, label, icon: Icon }) => (
        <Link
          key={href}
          href={href}
          className={`flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors ${
            pathname === href
              ? "bg-secondary text-secondary-foreground font-medium"
              : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground"
          }`}
        >
          <Icon className="size-4" />
          {label}
        </Link>
      ))}
    </nav>
  );
}

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const mounted = useMounted();
  const token = useAuthStore((s) => s.token);
  const { data: user } = useCurrentUser();
  const logout = useLogout();

  useEffect(() => {
    if (mounted && !token) {
      router.replace("/login");
    }
  }, [mounted, token, router]);

  function handleLogout() {
    logout.mutate(undefined, {
      onSettled: () => router.replace("/"),
    });
  }

  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-56 shrink-0 border-r p-4 md:block">
        <div className="mb-6 px-3 text-sm font-semibold">Resume Roaster</div>
        <SidebarNav />
        <div className="mt-auto pt-8">
          {user ? (
            <div className="px-3 text-xs text-muted-foreground">
              {user.email}
            </div>
          ) : null}
          <Button
            variant="ghost"
            size="sm"
            className="mt-2 w-full justify-start"
            onClick={handleLogout}
            disabled={logout.isPending}
          >
            <LogOut className="size-4" />
            Log out
          </Button>
        </div>
      </aside>
      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}
