"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { apiFetch } from "@/lib/api-client";
import { useAuthStore } from "@/stores/auth-store";
import { useLogout } from "@/hooks/queries/use-auth";
import { LogOut, User, Edit } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useCurrentUser } from "@/hooks/queries/use-auth";
import { Sidebar } from "@/components/layout/Sidebar";

export default function ProfilePage() {
  const { data: user, isPending: userPending, isError: userError, error: userErrorMsg } = useCurrentUser();
  const logout = useLogout();

  if (userPending) {
    return (
      <div className="flex items-center justify-center h-64 bg-background">
        <div className="space-y-4">
          <Skeleton className="h-12 w-12 rounded-full" />
          <Skeleton className="h-6 w-48 rounded-b" />
        </div>
      </div>
    );
  }

  if (userError) {
    return (
      <div className="bg-card border border-border rounded-2xl p-6 max-w-md mx-auto text-center">
        <p className="font-medium text-error">Could not load profile</p>
        <p className="text-muted-foreground mt-2">
          {userErrorMsg instanceof Error ? userErrorMsg.message : "An unexpected error occurred."}
        </p>
        <Button variant="outline" onClick={() => window.location.reload()}>Retry</Button>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex items-center justify-center h-64 bg-background">
        <p className="text-muted-foreground mb-4">
          Please <a href="/login" className="underline font-medium">log in</a> first.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-background min-h-screen p-6">
      <Sidebar />

      <div className="max-w-2xl mx-auto">
        {/* Profile card */}

        <div className="bg-card border border-border rounded-2xl p-8 md:p-10 shadow-sm">
          <div className="text-center mb-8">

            {/* Avatar */}
            <div className="mx-auto mb-4">
              <div className="flex items-center justify-center h-20 w-20 rounded-2xl bg-muted">
                <User className="size-6 text-primary" />
              </div>
              <div className="absolute -inset-0.5 rounded-full bg-primary border-2 border-background" />
            </div>

            <h2 className="mt-6 text-2xl font-bold tracking-tight">{user.name}</h2>
            <p className="mt-2 text-lg text-muted-foreground">{user.email}</p>

            {/* Action buttons */}
            <div className="mt-6 flex gap-3 flex-wrap justify-center">
              <Button
                variant="outline"
                size="icon"
                aria-label="Edit profile"
                onClick={() => window.alert("Edit profile clicked")}
              >
                <Edit className="size-4" />
              </Button>
              <Button variant="secondary" size="sm" onClick={() => logout.mutate()}>
                <LogOut className="size-4 mr-2" />Log out
              </Button>
            </div>
          </div>
        </div>

        {/* Account info */}
        <div className="grid gap-4 mt-8">
          <div>
            <p className="text-sm font-medium text-muted-foreground">Account</p>
            <p className="mt-1 text-base font-medium">{user.email}</p>
          </div>

          <div>
            <p className="text-sm font-medium text-muted-foreground">Member since</p>
            <p className="mt-1 text-base">{new Date(user.created_at).toLocaleDateString()}</p>
          </div>
        </div>

        {/* Security section */}
        <div className="mt-8">
          <h3 className="font-medium mb-4">Security</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-muted/50 rounded-lg p-4">
              <p className="text-xs font-medium text-muted-foreground">Active sessions</p>
              <p className="mt-1 font-medium">1 session</p>
            </div>
            <div className="bg-muted/50 rounded-lg p-4">
              <p className="text-xs font-medium text-muted-foreground">Password</p>
              <p className="mt-1 font-medium text-link">Change password</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}