"use client";

import { motion, type Variants } from "framer-motion";
import {
  ArrowRight,
  BadgeCheck,
  FileUp,
  Flame,
  Gauge,
  Lock,
  Plus,
  ScrollText,
  Users,
} from "lucide-react";
import Link from "next/link";

import { ScoreRing } from "@/components/analysis/score-ring";
import { LandingNavbar } from "@/components/layout/landing-navbar";
import { TaglineReveal } from "@/components/landing/tagline-reveal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useCurrentUser } from "@/hooks/queries/use-auth";

/** Weighted, decelerating curve used by every entrance on the page. */
const EASE: [number, number, number, number] = [0.22, 1, 0.36, 1];

const fadeUp: Variants = {
  hidden: { opacity: 0, y: 32 },
  show: { opacity: 1, y: 0, transition: { duration: 0.7, ease: EASE } },
};
const stagger: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06 } },
};

function reveal() {
  return {
    initial: "hidden" as const,
    whileInView: "show" as const,
    viewport: { once: true, margin: "-40px" },
  };
}

/** The page has one primary action; this is the only filled button on it. */
function PrimaryCta({ size = "lg" }: { size?: "default" | "lg" }) {
  const { data: user } = useCurrentUser();
  return (
    <Button size={size} asChild>
      <Link href={user ? "/dashboard" : "/register"}>
        {user ? "Open dashboard" : "Get roasted, free"}
        <ArrowRight className="size-4" />
      </Link>
    </Button>
  );
}

const PROOF_STATS = [
  { value: "4", label: "expert evaluators" },
  { value: "8", label: "deterministic checks" },
  { value: "50 / 50", label: "hybrid scoring" },
];

/** A CSS-built mock of the result page, no screenshot needed. */
function ProductMock() {
  return (
    <div className="relative mx-auto mt-10 max-w-3xl">
      <div className="glass-card relative overflow-hidden rounded-2xl shadow-2xl">
        {/* Fake browser chrome */}
        <div className="flex items-center gap-1.5 border-b border-border px-4 py-3">
          <span className="size-2.5 rounded-full bg-destructive/70" />
          <span className="size-2.5 rounded-full bg-yellow-500/70" />
          <span className="size-2.5 rounded-full bg-primary/70" />
          <span className="ml-3 rounded-md bg-muted px-2 py-0.5 caption-5 text-muted-foreground">
            airoast.dev/analysis
          </span>
        </div>

        <div className="grid gap-4 p-4 sm:grid-cols-[auto_1fr] sm:items-center">
          <div className="flex flex-col items-center gap-1">
            <ScoreRing score={69} size={96} />
            <span className="caption-5 text-muted-foreground">roast score</span>
          </div>
          <div className="min-w-0">
            <p className="mb-2 flex items-center gap-2 title-3">
              <Flame className="size-4 text-primary" aria-hidden />
              The roast
            </p>
            <p className="line-clamp-4 body-6 text-muted-foreground">
              &ldquo;Let us address the elephant in the room: you claim five
              years of experience, but your work history began in 2021, and your
              skills section is playing keyword bingo. Docker, Redis,
              Kubernetes, with zero evidence you have touched any of them on the
              job. Fortunately, your quantified FastAPI work is genuinely
              impressive...&rdquo;
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
      "The recruiter screen, ATS readiness, technical evidence, and writing quality run in parallel.",
    chips: ["Recruiter", "ATS", "Technical", "Writing"],
    wide: true,
  },
  {
    icon: Gauge,
    title: "Explainable hybrid scoring",
    description:
      "Half deterministic checks, half expert ratings mapped to fixed bands. The same resume scores the same every time.",
  },
  {
    icon: Flame,
    title: "Brutal, never generic",
    description:
      "Every finding quotes your resume and explains why a recruiter would care. No advice to add more keywords.",
  },
  {
    icon: Lock,
    title: "Private by design",
    description:
      "Token auth, per user file storage, and resumes you can actually delete.",
  },
];

const PROBLEMS = [
  {
    title: "Claims without evidence",
    description:
      "Docker, Redis, Kubernetes on the skills line, and nothing in the history that shows where you used them.",
  },
  {
    title: "Timelines that do not add up",
    description:
      "Five years of experience in a work history that starts in 2021. Recruiters catch it in the first pass.",
  },
  {
    title: "Feedback you cannot act on",
    description:
      "A score out of 100 tells you nothing about which sentence to rewrite before the next application.",
  },
];

const STEPS = [
  {
    icon: FileUp,
    title: "Drop your resume",
    description:
      "PDF or DOCX up to 10 MB. Parsing and the quality gate run immediately.",
  },
  {
    icon: Users,
    title: "Four experts review it",
    description:
      "The evaluators work in parallel. One failing never blocks the others.",
  },
  {
    icon: ScrollText,
    title: "Get the roast",
    description:
      "Your score, every weakness ranked by severity, a written roast, and the lines to rewrite.",
  },
];

const FAQ = [
  {
    question: "What do I actually get?",
    answer:
      "A score from 0 to 100, a written roast, findings ranked by severity, a fix plan that rewrites weak lines, and the four expert verdicts behind the score.",
  },
  {
    question: "How is the score calculated?",
    answer:
      "Half comes from eight deterministic checks on the file and the text. Half comes from four expert ratings mapped to fixed bands, so the same resume and the same posting produce the same score.",
  },
  {
    question: "Which files can I upload?",
    answer:
      "PDF or DOCX up to 10 MB, with at least 100 words of extractable text. A scanned image without a text layer is rejected before any model runs.",
  },
  {
    question: "Can I target a specific job?",
    answer:
      "Yes. Paste the job description or pick one of eight role profiles. The evaluators and the fix plan then read your resume against that target.",
  },
  {
    question: "How long does a roast take?",
    answer:
      "Usually two to three minutes. The page updates as each stage finishes, so you can watch the panel work instead of staring at a spinner.",
  },
  {
    question: "Do you keep my resume?",
    answer:
      "It stays in your account until you delete it. Deleting removes the stored file and hides the record; only you can open your uploads.",
  },
  {
    question: "What happens if a model fails?",
    answer:
      "The run is marked incomplete and the report is withheld instead of shown half finished. Start another roast and the panel runs again.",
  },
  {
    question: "Which models run the panel?",
    answer:
      "A hosted model chain configured on the server. When one model hits a quota error the next takes over, so a single provider outage does not stop a roast.",
  },
  {
    question: "Is it free?",
    answer: "Three roasts per day on the free tier, no card required.",
  },
];

/** Structured data so the FAQ can surface as a rich result. */
const FAQ_JSON_LD = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: FAQ.map((item) => ({
    "@type": "Question",
    name: item.question,
    acceptedAnswer: { "@type": "Answer", text: item.answer },
  })),
};

function SectionLabel({ children }: { children: string }) {
  return <p className="caption-3 text-muted-foreground">{children}</p>;
}

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(FAQ_JSON_LD) }}
      />
      <LandingNavbar />

      <main className="flex-1 overflow-x-clip">
        {/* Hero */}
        <section className="relative px-4 pt-10 pb-10 text-center">
          <div
            className="bg-glow-ember pointer-events-none absolute inset-x-0 -top-32 mx-auto h-[480px] max-w-4xl"
            aria-hidden
          />
          <motion.div
            variants={stagger}
            initial="hidden"
            animate="show"
            className="relative mx-auto max-w-[680px]"
          >
            <motion.div variants={fadeUp}>
              <Badge variant="outline" className="border-primary/40 text-primary">
                <BadgeCheck className="mr-1 size-3.5" />
                Four AI experts. Zero mercy.
              </Badge>
            </motion.div>
            <motion.h1
              variants={fadeUp}
              className="mt-3 heading-3 text-balance sm:heading-1"
            >
              <span className="block">Your resume,</span>
              <span className="block text-gradient-ember">
                brutally roasted.
              </span>
            </motion.h1>
            <motion.p
              variants={fadeUp}
              className="mx-auto mt-4 max-w-[560px] body-7 text-muted-foreground"
            >
              Upload a resume and four specialised evaluators tear it apart: the
              recruiter screen, ATS parsing, technical evidence, and writing
              quality. You get one honest score, every weakness ranked, and the
              lines to rewrite.
            </motion.p>
            <motion.div variants={fadeUp} className="mt-6">
              <PrimaryCta />
              <p className="mt-3 caption-5 text-muted-foreground">
                3 free roasts per day. No card. About two minutes.
              </p>
            </motion.div>
            <motion.dl
              variants={fadeUp}
              className="mx-auto mt-8 grid max-w-sm grid-cols-3 gap-4"
            >
              {PROOF_STATS.map((stat) => (
                <div key={stat.label}>
                  <dt className="sr-only">{stat.label}</dt>
                  <dd className="font-mono text-xl font-semibold tabular-nums">
                    {stat.value}
                  </dd>
                  <dd className="mt-1 caption-5 text-muted-foreground">
                    {stat.label}
                  </dd>
                </div>
              ))}
            </motion.dl>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 32 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.25, ease: EASE }}
          >
            <ProductMock />
          </motion.div>
        </section>

        {/* Problem to solution */}
        <section className="mx-auto mt-20 max-w-5xl px-4 scroll-mt-24">
          <motion.div {...reveal()} className="max-w-[680px]">
            <SectionLabel>The problem</SectionLabel>
            <h2 className="mt-2 heading-4 text-balance">
              The advice you already have is not working.
            </h2>
            <p className="mt-3 body-3 text-muted-foreground">
              Most tools return the same three words: add more keywords.
              Recruiters reject in the first six seconds for reasons a keyword
              list cannot see, and none of them is the list itself.
            </p>
          </motion.div>

          <motion.div
            {...reveal()}
            variants={stagger}
            className="mt-8 grid gap-6 md:grid-cols-3"
          >
            {PROBLEMS.map((problem) => (
              <motion.div key={problem.title} variants={fadeUp}>
                <h3 className="title-3">{problem.title}</h3>
                <p className="mt-2 body-6 text-muted-foreground">
                  {problem.description}
                </p>
              </motion.div>
            ))}
          </motion.div>

          <motion.p
            {...reveal()}
            className="mt-6 max-w-[680px] body-3"
          >
            The panel names the sentence, the reason, and the rewrite. That is
            the whole difference.
          </motion.p>
        </section>

        {/* Benefits bento */}
        <section
          id="features"
          className="mx-auto mt-20 max-w-5xl px-4 scroll-mt-24"
        >
          <motion.h2
            {...reveal()}
            className="text-center heading-4 text-balance"
          >
            Not one generic chat answer. A pipeline.
          </motion.h2>
          <motion.div
            {...reveal()}
            variants={stagger}
            className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
          >
            {FEATURES.map((feature) => (
              <motion.div
                key={feature.title}
                variants={fadeUp}
                className={`flex h-full flex-col rounded-xl border border-border bg-card p-6 ${
                  feature.wide ? "sm:col-span-2 lg:col-span-2" : ""
                }`}
              >
                <span className="flex size-10 items-center justify-center rounded-xl bg-primary/15 text-primary">
                  <feature.icon className="size-5" />
                </span>
                <h3 className="mt-4 title-3">{feature.title}</h3>
                <p className="mt-2 body-6 text-muted-foreground">
                  {feature.description}
                </p>
                {feature.chips && (
                  <div className="mt-auto flex flex-wrap gap-2 pt-4">
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
              className="rounded-xl border border-primary/30 bg-card p-6"
            >
              <span className="flex size-10 items-center justify-center rounded-xl bg-primary/20 text-primary">
                <Flame className="size-5" />
              </span>
              <h3 className="mt-4 title-3">Ready when you are</h3>
              <p className="mt-2 body-6 text-muted-foreground">
                Three free roasts per day. Drop a resume and watch the experts
                work, live.
              </p>
              <div className="mt-4">
                <PrimaryCta size="default" />
              </div>
            </motion.div>
          </motion.div>
        </section>

        {/* Tagline moment */}
        <section className="mx-auto mt-20 max-w-5xl px-4">
          <TaglineReveal
            lines={[
              "A resume is a claim.",
              "Evidence is the only thing that survives the screen.",
            ]}
          />
        </section>

        {/* How it works */}
        <section
          id="how-it-works"
          className="mx-auto mt-20 max-w-5xl px-4 scroll-mt-24"
        >
          <motion.h2
            {...reveal()}
            className="text-center heading-4 text-balance"
          >
            Three minutes to a better resume
          </motion.h2>
          <motion.div
            {...reveal()}
            variants={stagger}
            className="mt-8 grid gap-6 md:grid-cols-3"
          >
            {STEPS.map((step, index) => (
              <motion.div key={step.title} variants={fadeUp} className="relative">
                <span className="absolute -top-3 -left-2 text-5xl font-semibold text-primary/15 select-none">
                  {index + 1}
                </span>
                <span className="relative flex size-10 items-center justify-center rounded-xl bg-primary/15 text-primary">
                  <step.icon className="size-5" />
                </span>
                <h3 className="mt-4 title-3">{step.title}</h3>
                <p className="mt-2 body-6 text-muted-foreground">
                  {step.description}
                </p>
              </motion.div>
            ))}
          </motion.div>
        </section>

        {/* Proof: a real run, not a testimonial */}
        <section className="mx-auto mt-20 max-w-5xl px-4">
          <motion.div
            {...reveal()}
            className="grid gap-6 rounded-xl border border-border bg-card p-6 md:grid-cols-[auto_minmax(0,1fr)] md:items-center"
          >
            <p className="font-mono text-4xl font-semibold tabular-nums">
              77 <span className="text-muted-foreground">to</span> 66.44
            </p>
            <div>
              <h2 className="heading-4 text-balance">
                One real resume, scored by both panels.
              </h2>
              <p className="mt-2 body-6 text-muted-foreground">
                The first version of this panel gave the founder&rsquo;s resume a
                77. The 2026 panel gave the same file 66.44 and caught three
                defects the earlier version missed.
              </p>
              <ul className="mt-3 flex flex-wrap gap-2">
                {[
                  "Bracket placeholders left in the file",
                  "An employment date in 2026",
                  "Words glued together by the extractor",
                ].map((defect) => (
                  <li
                    key={defect}
                    className="rounded-md border border-border px-2 py-1 caption-5 text-muted-foreground"
                  >
                    {defect}
                  </li>
                ))}
              </ul>
              <p className="mt-3 caption-5 text-muted-foreground">
                Verified run, 30 October 2026.
              </p>
            </div>
          </motion.div>
        </section>

        {/* FAQ */}
        <section id="faq" className="mx-auto mt-20 max-w-3xl px-4 scroll-mt-24">
          <motion.div {...reveal()}>
            <SectionLabel>Questions</SectionLabel>
            <h2 className="mt-2 heading-4 text-balance">
              What people ask before the first roast
            </h2>
          </motion.div>
          <motion.div {...reveal()} className="mt-6">
            {FAQ.map((item) => (
              <details
                key={item.question}
                className="group border-b border-border py-4"
              >
                <summary className="flex cursor-pointer list-none items-center justify-between gap-4 title-3 focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none">
                  {item.question}
                  <Plus
                    className="size-4 shrink-0 text-muted-foreground transition-transform duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] group-open:rotate-45"
                    aria-hidden
                  />
                </summary>
                <p className="mt-3 body-6 text-muted-foreground">
                  {item.answer}
                </p>
              </details>
            ))}
          </motion.div>
        </section>

        {/* Final CTA */}
        <section className="mx-auto mt-20 max-w-5xl px-4 pb-20">
          <motion.div
            {...reveal()}
            className="rounded-xl border border-primary/30 bg-card p-8 text-center"
          >
            <Flame className="mx-auto size-8 text-primary" aria-hidden />
            <h2 className="mt-4 heading-4 text-balance">
              Your resume can take it.
            </h2>
            <p className="mx-auto mt-3 max-w-[560px] body-3 text-muted-foreground">
              Honest feedback stings for a minute. A rejected application stings
              for weeks.
            </p>
            <div className="mt-6">
              <PrimaryCta />
            </div>
          </motion.div>
        </section>
      </main>

      <footer className="border-t border-border py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-4 caption-5 text-muted-foreground sm:flex-row">
          <span className="flex items-center gap-2">
            <Flame className="size-4 text-primary" aria-hidden />
            Resume Roaster
          </span>
          <nav aria-label="Legal" className="flex items-center gap-4">
            <Link href="/privacy" className="transition-colors hover:text-foreground">
              Privacy
            </Link>
            <Link href="/terms" className="transition-colors hover:text-foreground">
              Terms
            </Link>
            <span>&copy; 2026</span>
          </nav>
        </div>
      </footer>
    </div>
  );
}
