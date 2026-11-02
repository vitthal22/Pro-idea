"use client";

import { LogOut, User } from "lucide-react";

import { ThemeToggle } from "@/components/theme-toggle";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useCurrentUser, useLogout } from "@/hooks/queries/use-auth";

export default function ProfilePage() {
  const {
    data: user,
    isPending: userPending,
    isError: userError,
    error: userErrorMsg,
  } = useCurrentUser();
  const logout = useLogout();

  if (userPending) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-32 w-full rounded-2xl" />
        <Skeleton className="h-24 w-full rounded-2xl" />
      </div>
    );
  }

  if (userError) {
    return (
      <div className="mx-auto max-w-md rounded-2xl border border-border bg-card p-6 text-center">
        <p className="font-medium text-destructive">Could not load profile</p>
        <p className="mt-2 text-muted-foreground">
          {userErrorMsg instanceof Error
            ? userErrorMsg.message
            : "An unexpected error occurred."}
        </p>
        <Button variant="outline" onClick={() => window.location.reload()}>
          Retry
        </Button>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="mx-auto max-w-md rounded-2xl border border-border bg-card p-8 text-center">
        <p className="text-muted-foreground">
          Please{" "}
          <a href="/login" className="font-medium underline">
            log in
          </a>{" "}
          first.
        </p>
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Profile" description="Your account at a glance." />

      <div className="rounded-2xl border border-border bg-card p-8 text-center">
        <div className="mx-auto mb-4 flex size-20 items-center justify-center rounded-2xl bg-primary/15 text-primary">
          <User className="size-8" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight">{user.name}</h2>
        <p className="mt-1 text-muted-foreground">{user.email}</p>
        <div className="mt-4 text-sm text-muted-foreground">
          Member since {new Date(user.created_at).toLocaleDateString()}
        </div>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        <div className="rounded-2xl border border-border bg-card p-5">
          <p className="text-sm font-medium text-muted-foreground">Appearance</p>
          <div className="mt-3 flex items-center justify-between">
            <span className="text-sm">Theme</span>
            <ThemeToggle />
          </div>
        </div>
        <div className="rounded-2xl border border-border bg-card p-5">
          <p className="text-sm font-medium text-muted-foreground">Session</p>
          <Button
            variant="outline"
            size="sm"
            className="mt-3 w-full justify-start"
            onClick={() => logout.mutate()}
            disabled={logout.isPending}
          >
            <LogOut className="size-4" />
            Log out
          </Button>
        </div>
      </div>
    </div>
  );
}
