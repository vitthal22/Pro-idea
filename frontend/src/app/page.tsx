"use client";

import { motion, type Variants } from "framer-motion";
import {
  ArrowRight,
  BadgeCheck,
  FileUp,
  Flame,
  Gauge,
  Lock,
  ScrollText,
  Users,
} from "lucide-react";
import Link from "next/link";

import { ScoreRing } from "@/components/analysis/score-ring";
import { LandingNavbar } from "@/components/layout/landing-navbar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useCurrentUser } from "@/hooks/queries/use-auth";

const fadeUp: Variants = {
  hidden: { opacity: 0, y: 18 },
  show: { opacity: 1, y: 0, transition: { duration: 0.45, ease: "easeOut" } },
};
const stagger: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.09 } },
};

function reveal() {
  return {
    initial: "hidden" as const,
    whileInView: "show" as const,
    viewport: { once: true, margin: "-80px" },
  };
}

function AuthButtons({ size = "lg" }: { size?: "default" | "lg" }) {
  const { data: user } = useCurrentUser();
  if (user) {
    return (
      <Button size={size} asChild>
        <Link href="/dashboard">
          Open dashboard
          <ArrowRight className="size-4" />
        </Link>
      </Button>
    );
  }
  return (
    <div className="flex flex-wrap justify-center gap-3">
      <Button size={size} asChild>
        <Link href="/register">Get roasted — free</Link>
      </Button>
      <Button size={size} variant="outline" asChild>
        <Link href="/login">Log in</Link>
      </Button>
    </div>
  );
}

/** A CSS-built mock of the result page — no screenshot needed. */
function ProductMock() {
  return (
    <div className="relative mx-auto mt-14 max-w-3xl">
      <div
        className="bg-glow-ember pointer-events-none absolute -inset-x-8 -top-10 h-40"
        aria-hidden
      />
      <div className="glass-card relative overflow-hidden rounded-2xl shadow-2xl">
        {/* Fake browser chrome */}
        <div className="flex items-center gap-1.5 border-b border-border px-4 py-3">
          <span className="size-2.5 rounded-full bg-destructive/70" />
          <span className="size-2.5 rounded-full bg-yellow-500/70" />
          <span className="size-2.5 rounded-full bg-primary/70" />
          <span className="ml-3 rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground">
            airoast.dev/analysis
          </span>
        </div>

        <div className="grid gap-6 p-6 sm:grid-cols-[auto_1fr] sm:items-center">
          <div className="flex flex-col items-center gap-1">
            <ScoreRing score={69} size={110} />
            <span className="text-xs text-muted-foreground">roast score</span>
          </div>
          <div className="min-w-0">
            <p className="mb-2 flex items-center gap-2 text-sm font-semibold">
              <Flame className="size-4 text-primary" aria-hidden />
              The roast
            </p>
            <p className="line-clamp-4 text-sm leading-relaxed text-muted-foreground">
              &ldquo;Let us address the elephant in the room: you claim five
              years of experience, but your work history began in 2021 — and
              your skills section is playing keyword bingo. Docker, Redis,
              Kubernetes… with zero evidence you have touched any of them on
              the job. Fortunately, your quantified FastAPI work is genuinely
              impressive…&rdquo;
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Badge variant="destructive">1 critical issue</Badge>
              <Badge variant="secondary">6 warnings</Badge>
              <Badge variant="outline" className="border-primary/40 text-primary">
                6 fixes
              </Badge>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

const FEATURES = [
  {
    icon: Users,
    title: "Four expert evaluators",
    description:
      "A recruiter's six-second screen, ATS parse readiness, technical evidence check, and writing-quality review — running in parallel.",
    chips: ["Recruiter", "ATS", "Technical", "Writing"],
    wide: true,
  },
  {
    icon: Gauge,
    title: "Explainable hybrid scoring",
    description:
      "50% deterministic checks, 50% expert ratings mapped to fixed bands. Same resume, same score — every time.",
  },
  {
    icon: Flame,
    title: "Brutal, never generic",
    description:
      "Every finding quotes your resume and explains why a recruiter would care. No 'consider adding more keywords' filler.",
  },
  {
    icon: Lock,
    title: "Private by design",
    description:
      "Token-based auth, per-user file storage, and soft-deleted resumes that actually disappear.",
  },
];

function HowItWorks() {
  const steps = [
    {
      icon: FileUp,
      title: "Drop your resume",
      description: "PDF or DOCX, up to 10 MB. Parsing and quality checks run instantly.",
    },
    {
      icon: Users,
      title: "Four experts review it",
      description:
        "The evaluators work in parallel; one failing never blocks the others.",
    },
    {
      icon: ScrollText,
      title: "Get the roast",
      description:
        "Your score, every weakness ranked by severity, and a brutally honest narrative — plus what to keep.",
    },
  ];

  return (
    <section className="mx-auto mt-28 max-w-4xl px-4">
      <motion.h2
        {...reveal()}
        className="text-center text-3xl font-bold tracking-tight"
      >
        Three minutes to a better resume
      </motion.h2>
      <motion.div
        {...reveal()}
        variants={stagger}
        className="mt-10 grid gap-6 md:grid-cols-3"
      >
        {steps.map((step, index) => (
          <motion.div key={step.title} variants={fadeUp} className="relative">
            <span className="absolute -top-3 -left-2 text-5xl font-bold text-primary/15 select-none">
              {index + 1}
            </span>
            <span className="relative flex size-10 items-center justify-center rounded-xl bg-primary/15 text-primary">
              <step.icon className="size-5" />
            </span>
            <h3 className="mt-4 font-semibold">{step.title}</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              {step.description}
            </p>
          </motion.div>
        ))}
      </motion.div>
    </section>
  );
}

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <LandingNavbar />

      <main className="flex-1 overflow-x-clip">
        {/* Hero */}
        <section className="relative px-4 pt-20 pb-16 text-center">
          <div
            className="bg-glow-ember pointer-events-none absolute inset-x-0 -top-32 mx-auto h-[480px] max-w-4xl"
            aria-hidden
          />
          <motion.div
            variants={stagger}
            initial="hidden"
            animate="show"
            className="relative mx-auto max-w-3xl"
          >
            <motion.div variants={fadeUp}>
              <Badge variant="outline" className="border-primary/40 text-primary">
                <BadgeCheck className="mr-1 size-3.5" />
                Four AI experts. Zero mercy. Full feedback.
              </Badge>
            </motion.div>
            <motion.h1
              variants={fadeUp}
              className="mt-5 text-4xl font-bold tracking-tight text-balance sm:text-6xl"
            >
              Your resume, <span className="text-gradient-ember">brutally roasted</span>.
            </motion.h1>
            <motion.p
              variants={fadeUp}
              className="mx-auto mt-5 max-w-2xl text-lg text-muted-foreground"
            >
              Upload a resume and four specialized AI evaluators — recruiter,
              ATS, technical, writing — tear it apart. You get one honest
              score, every weakness ranked, and a fix list. Constructive,
              never generic.
            </motion.p>
            <motion.div variants={fadeUp} className="mt-8">
              <AuthButtons />
              <p className="mt-4 text-xs text-muted-foreground">
                3 free roasts • No credit card • About 2 minutes
              </p>
            </motion.div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 32 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.35, ease: "easeOut" }}
          >
            <ProductMock />
          </motion.div>
        </section>

        {/* Features bento */}
        <section className="mx-auto mt-24 max-w-5xl px-4">
          <motion.h2
            {...reveal()}
            className="text-center text-3xl font-bold tracking-tight"
          >
            Not one generic chat answer.{" "}
            <span className="text-gradient-ember">A pipeline.</span>
          </motion.h2>
          <motion.div
            {...reveal()}
            variants={stagger}
            className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
          >
            {FEATURES.map((feature) => (
              <motion.div
                key={feature.title}
                variants={fadeUp}
                className={`rounded-2xl border border-border bg-card p-6 ${
                  feature.wide ? "sm:col-span-2 lg:col-span-2" : ""
                }`}
              >
                <span className="flex size-10 items-center justify-center rounded-xl bg-primary/15 text-primary">
                  <feature.icon className="size-5" />
                </span>
                <h3 className="mt-4 font-semibold">{feature.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  {feature.description}
                </p>
                {feature.chips && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {feature.chips.map((chip) => (
                      <Badge key={chip} variant="secondary">
                        {chip}
                      </Badge>
                    ))}
                  </div>
                )}
              </motion.div>
            ))}
            <motion.div
              variants={fadeUp}
              className="rounded-2xl border border-primary/30 bg-gradient-to-br from-primary/15 via-primary/5 to-transparent p-6"
            >
              <span className="flex size-10 items-center justify-center rounded-xl bg-primary/20 text-primary">
                <Flame className="size-5" />
              </span>
              <h3 className="mt-4 font-semibold">Ready when you are</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                Three free roasts. Drop a resume and watch the experts work —
                live.
              </p>
              <Button asChild size="sm" className="mt-4">
                <Link href="/register">
                  Start free
                  <ArrowRight className="size-4" />
                </Link>
              </Button>
            </motion.div>
          </motion.div>
        </section>

        <HowItWorks />

        {/* Final CTA */}
        <section className="mx-auto mt-28 max-w-4xl px-4">
          <motion.div
            {...reveal()}
            className="relative overflow-hidden rounded-3xl border border-primary/30 p-10 text-center"
          >
            <div
              className="bg-glow-ember pointer-events-none absolute inset-0"
              aria-hidden
            />
            <div className="relative">
              <Flame className="mx-auto size-8 text-primary" aria-hidden />
              <h2 className="mt-4 text-3xl font-bold tracking-tight">
                Your resume can take it.
              </h2>
              <p className="mx-auto mt-3 max-w-xl text-muted-foreground">
                Honest feedback stings for a minute. A rejected application
                stings for weeks.
              </p>
              <div className="mt-7">
                <AuthButtons />
              </div>
            </div>
          </motion.div>
        </section>
      </main>

      <footer className="mt-24 border-t border-border py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-4 text-sm text-muted-foreground sm:flex-row">
          <span className="flex items-center gap-2">
            <Flame className="size-4 text-primary" aria-hidden />
            Resume Roaster
          </span>
          <span>Brutally honest resume feedback • © 2026</span>
        </div>
      </footer>
    </div>
  );
}
