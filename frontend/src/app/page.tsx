"use client";

import { Flame, Gauge, ListChecks, Target } from "lucide-react";
import Link from "next/link";

import { Navbar } from "@/components/layout/Navbar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useCurrentUser } from "@/hooks/queries/use-auth";

function AuthButtons() {
  const { data: user } = useCurrentUser();
  if (user) {
    return (
      <Button size="lg" asChild>
        <Link href="/dashboard">Open dashboard</Link>
      </Button>
    );
  }
  return (
    <div className="flex gap-3">
      <Button size="lg" asChild>
        <Link href="/register">Get started</Link>
      </Button>
      <Button size="lg" variant="outline" asChild>
        <Link href="/login">Log in</Link>
      </Button>
    </div>
  );
}

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-16">
        <section className="mx-auto max-w-2xl text-center">
          <Badge variant="secondary" className="mb-4">
            Multi-evaluator AI pipeline
          </Badge>
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
            Your resume, brutally roasted.
          </h1>
          <p className="text-muted-foreground mt-4 text-lg">
            Upload a resume, pick an analysis mode, and get scores, critical
            issues, warnings, and actionable improvements — from five
            specialized AI evaluators, not one generic chat answer.
          </p>
          <div className="mt-8 flex justify-center">
            <AuthButtons />
          </div>
        </section>

        <section className="mt-20 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader>
              <Flame className="mb-2 size-6 text-primary" />
              <CardTitle>Brutal, not mean</CardTitle>
              <CardDescription>
                Honest feedback that tells you what a recruiter actually
                thinks — then how to fix it.
              </CardDescription>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <ListChecks className="mb-2 size-6 text-primary" />
              <CardTitle>Hybrid scoring</CardTitle>
              <CardDescription>
                50% deterministic checks, 50% AI assessment. Reproducible and
                explainable.
              </CardDescription>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <Target className="mb-2 size-6 text-primary" />
              <CardTitle>Role &amp; JD matching</CardTitle>
              <CardDescription>
                Analyze against a target role or a full job description — not
                just generic advice.
              </CardDescription>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <Gauge className="mb-2 size-6 text-primary" />
              <CardTitle>Structured reports</CardTitle>
              <CardDescription>
                Scores, critical issues, warnings, and suggestions in a clear,
                actionable report.
              </CardDescription>
            </CardHeader>
          </Card>
        </section>
      </main>
    </div>
  );
}
