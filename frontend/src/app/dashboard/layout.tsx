"use client";

import { ClipboardList, LogOut, Upload, User, Settings, Heart } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { useMounted } from "@/hooks/use-mounted";
import { useCurrentUser, useLogout } from "@/hooks/queries/use-auth";
import { useAuthStore } from "@/stores/auth-store";
import { Sidebar } from "@/components/layout/Sidebar";

const NAV_ITEMS = [
  { href: "/dashboard", label: "History", icon: ClipboardList },
  { href: "/upload", label: "Upload", icon: Upload },
  { href: "/profile", label: "Profile", icon: User },
];

export function SidebarNav() {
  const pathname = usePathname();
  return (
    <nav className="grid gap-2 p-2 rounded-lg border border-border bg-card">
      {NAV_ITEMS.map(({ href, label, icon: Icon }) => (
        <Link
          key={href}
          href={href}
          className={`flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors ${pathname === href ? "bg-primary text-primary-foreground font-medium" : "text-muted-foreground hover:bg-primary/60 hover:text-primary"}`}
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
    <div className="min-h-screen bg-background">
      <div className="flex min-h-screen">
        <aside className="w-64 flex-shrink-0 bg-card border-r border-border">
          <Sidebar />
        </aside>

        <main className="flex-1 p-6 md:p-8">{children}</main>
      </div>
    </div>
  );
}