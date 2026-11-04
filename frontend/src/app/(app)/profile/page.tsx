"use client";

import { LogOut, User } from "lucide-react";

import { ThemeToggle } from "@/components/theme-toggle";
import { PageHeader } from "@/components/layout/page-header";
import { ErrorState } from "@/components/shared/ErrorState";
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

  const header = (
    <PageHeader title="Profile" description="Your account at a glance." />
  );

  if (userPending) {
    return (
      <div className="w-full max-w-2xl space-y-4">
        {header}
        <Skeleton className="h-24 w-full rounded-xl" />
        <Skeleton className="h-28 w-full rounded-xl" />
      </div>
    );
  }

  if (userError) {
    return (
      <div className="w-full max-w-2xl space-y-4">
        {header}
        <ErrorState
          title="Could not load profile"
          description={
            userErrorMsg instanceof Error
              ? userErrorMsg.message
              : "An unexpected error occurred."
          }
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="w-full max-w-2xl rounded-xl border border-border bg-card p-6 text-center">
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
    <div className="w-full max-w-2xl">
      {header}

      <div className="flex items-center gap-4 rounded-xl border border-border bg-card p-5">
        <div className="flex size-14 shrink-0 items-center justify-center rounded-xl bg-primary/15 text-primary">
          <User className="size-6" />
        </div>
        <div className="min-w-0 flex-1">
          <h2 className="truncate text-lg font-bold tracking-tight">
            {user.name}
          </h2>
          <p className="truncate text-sm text-muted-foreground">{user.email}</p>
        </div>
        <p className="hidden shrink-0 text-xs text-muted-foreground sm:block">
          Member since {new Date(user.created_at).toLocaleDateString()}
        </p>
      </div>

      <div className="mt-4 divide-y divide-border overflow-hidden rounded-xl border border-border bg-card">
        <div className="flex items-center justify-between gap-4 px-5 py-3">
          <div>
            <p className="text-sm font-medium">Appearance</p>
            <p className="text-xs text-muted-foreground">Light or dark theme.</p>
          </div>
          <ThemeToggle />
        </div>
        <div className="flex items-center justify-between gap-4 px-5 py-3">
          <div>
            <p className="text-sm font-medium">Session</p>
            <p className="text-xs text-muted-foreground">
              Sign out of this device.
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
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
