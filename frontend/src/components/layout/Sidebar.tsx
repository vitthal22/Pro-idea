"use client";

import { ClipboardList, LogOut, Upload, User, Settings, Heart } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { useMounted } from "@/hooks/use-mounted";
import { useCurrentUser, useLogout } from "@/hooks/queries/use-auth";
import { useAuthStore } from "@/stores/auth-store";

const NAV_ITEMS = [
  { href: "/dashboard", label: "History", icon: ClipboardList },
  { href: "/upload", label: "Upload", icon: Upload },
  { href: "/profile", label: "Profile", icon: User },
];

function SidebarNav() {
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

export function Sidebar() {
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
    <div className="w-64 flex-shrink-0 bg-card border-r border-border">
      <div className="p-4 md:p-6 border-b">
        <div className="flex items-center gap-3">
          <div className="bg-muted/50 rounded-full p-2">
            <User className="size-4" />
          </div>
          <div>
            <h3 className="font-medium">Resume Roaster</h3>
            <p className="text-xs text-muted-foreground">Demo User</p>
          </div>
        </div>
      </div>

      <SidebarNav />

      <div className="mt-auto p-4 md:p-6">
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-start"
          onClick={handleLogout}
          disabled={logout.isPending}
        >
          <LogOut className="size-4 mr-2" />Log out
        </Button>
      </div>
    </div>
  );
}