"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Check, FileText, X } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { ResumeDropzone } from "@/components/upload/ResumeDropzone";
import { PageHeader } from "@/components/layout/page-header";
import {
  ANALYSIS_MODES,
  CUSTOM_INSTRUCTIONS_MAX_CHARS,
  JD_MAX_CHARS,
  ROLE_OPTIONS,
  type AnalysisModeValue,
} from "@/lib/analysis-modes";
import { useUploadResume } from "@/hooks/mutations/use-upload";
import { useStartAnalysis } from "@/hooks/mutations/use-start-analysis";
import { useCurrentUser } from "@/hooks/queries/use-auth";
import { useAuthStore } from "@/stores/auth-store";

const MODE_OPTION_CLASS =
  "cursor-pointer rounded-xl border p-2 text-left transition-colors has-[[data-state=checked]]:border-primary has-[[data-state=checked]]:bg-primary/10 has-[:focus-visible]:ring-3 has-[:focus-visible]:ring-ring/50";

const PIPELINE_STEPS = [
  "Reading your resume",
  "Understanding its structure",
  "Four experts reviewing",
  "Calculating your score",
  "Writing the roast",
];

const REQUIREMENTS = [
  "PDF or DOCX, up to 10 MB.",
  "At least 100 words of real text.",
  "A scan without a text layer is rejected.",
];

/** Fills the right hand column on wide screens instead of leaving it blank. */
function UploadAside() {
  return (
    <aside className="max-w-2xl space-y-4 xl:sticky xl:top-6 xl:max-w-none">
      <section className="rounded-xl border border-border bg-card p-4">
        <h2 className="title-3">What happens next</h2>
        <ol className="mt-3 space-y-2">
          {PIPELINE_STEPS.map((step, index) => (
            <li key={step} className="flex items-center gap-3">
              <span className="font-mono text-xs text-muted-foreground">
                {index + 1}
              </span>
              <span className="body-6">{step}</span>
            </li>
          ))}
        </ol>
        <p className="mt-3 caption-5 text-muted-foreground">
          Two to three minutes. You can leave the page; the roast keeps running.
        </p>
      </section>

      <section className="rounded-xl border border-border bg-card p-4">
        <h2 className="title-3">Before you drop it</h2>
        <ul className="mt-3 space-y-2">
          {REQUIREMENTS.map((requirement) => (
            <li
              key={requirement}
              className="flex gap-2 body-6 text-muted-foreground"
            >
              <Check className="mt-1 size-3.5 shrink-0 text-primary" aria-hidden />
              <span>{requirement}</span>
            </li>
          ))}
        </ul>
      </section>
    </aside>
  );
}

export default function UploadPage() {
  const { isPending, isError, error } = useCurrentUser();
  const { token } = useAuthStore((s) => s);
  const router = useRouter();
  const upload = useUploadResume();
  const startAnalysis = useStartAnalysis();

  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [mode, setMode] = useState<AnalysisModeValue>("general");
  const [targetRole, setTargetRole] = useState("backend_dev");
  const [jobDescription, setJobDescription] = useState("");
  const [customInstructions, setCustomInstructions] = useState("");

  function handleFileSelected(selected: File) {
    setFile(selected);
    setFileError(null);
  }

  function handleFileError(message: string) {
    setFile(null);
    setFileError(message || null);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) {
      setFileError("Please choose a PDF or DOCX file first.");
      return;
    }
    if (mode === "role_based" && !targetRole) {
      setFileError("Pick a role for a role-based roast.");
      return;
    }
    if (mode === "jd_based" && !jobDescription.trim()) {
      setFileError("Paste the job description for a JD-based roast.");
      return;
    }
    // Auto-roast: the roast starts as soon as the upload succeeds.
    upload.mutate(file, {
      onSuccess: (resume) => {
        startAnalysis.mutate(
          {
            resumeId: resume.id,
            analysisType: mode,
            targetRole: mode === "role_based" ? targetRole : undefined,
            jobDescription: mode === "jd_based" ? jobDescription : undefined,
            customInstructions:
              mode === "custom" ? customInstructions : undefined,
          },
          {
            onSuccess: (created) => {
              toast.success("The roast has begun — four experts on the way.");
              router.push(`/analysis/${created.analysis_id}`);
            },
            onError: (err) =>
              setFileError(
                `Resume uploaded, but the roast could not start: ${
                  err instanceof Error ? err.message : "unknown error"
                }`,
              ),
          },
        );
      },
    });
  }

  if (!token) {
    return (
      <div className="mx-auto max-w-md rounded-xl border border-border bg-card p-6 text-center">
        <p className="font-medium">
          Please{" "}
          <a href="/login" className="font-medium underline">
            log in
          </a>{" "}
          to upload
        </p>
      </div>
    );
  }

  if (isPending) {
    return (
      <div className="mx-auto max-w-md rounded-xl border border-border bg-card p-6 text-center">
        <Skeleton className="mx-auto h-4 w-32" />
        <Skeleton className="mt-4 h-24 w-full rounded-xl" />
        <Skeleton className="mt-2 h-10 w-full rounded-lg" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="mx-auto max-w-md rounded-xl border border-border bg-card p-6 text-center">
        <p className="font-medium">Could not load your profile</p>
        <p className="mt-1 text-destructive">
          {error instanceof Error
            ? error.message
            : "An unexpected error occurred."}
        </p>
        <Button
          variant="outline"
          onClick={() => window.location.reload()}
          className="mt-4"
        >
          Retry
        </Button>
      </div>
    );
  }

  const uploadError =
    fileError ??
    (upload.error instanceof Error ? upload.error.message : null);
  const busy = upload.isPending || startAnalysis.isPending;

  return (
    <div className="w-full">
      <PageHeader
        title="Upload Resume"
        description="Pick how hard to roast, drop the file — the experts start automatically."
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_20rem] xl:items-start">
        <form
          onSubmit={handleSubmit}
          className="min-w-0 max-w-2xl space-y-4 xl:max-w-none"
        >
          <ResumeDropzone
            onFileSelected={handleFileSelected}
            onFileError={handleFileError}
            disabled={busy}
          />

          {file && (
            <div className="flex items-center gap-3 rounded-xl border border-primary/30 bg-primary/5 px-4 py-3">
              <FileText className="size-5 shrink-0 text-primary" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{file.name}</p>
                <p className="text-xs text-muted-foreground">
                  {Math.round(file.size / 1024)} KB
                </p>
              </div>
              {!busy && (
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  aria-label="Remove file"
                  onClick={() => {
                    setFile(null);
                    setFileError(null);
                  }}
                >
                  <X className="size-4" />
                </Button>
              )}
            </div>
          )}

          <div>
            <Label className="mb-2 block">Roast mode</Label>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {ANALYSIS_MODES.map((option) => (
                <label key={option.value} className={MODE_OPTION_CLASS}>
                  <input
                    type="radio"
                    name="analysis-mode"
                    value={option.value}
                    checked={mode === option.value}
                    onChange={() => setMode(option.value)}
                    disabled={busy}
                    className="sr-only"
                  />
                  <span className="block text-sm font-medium">{option.label}</span>
                  <span className="mt-0.5 block text-xs text-muted-foreground">
                    {option.hint}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {mode === "role_based" && (
            <div>
              <Label htmlFor="target-role" className="mb-2 block">
                Target role
              </Label>
              <Select value={targetRole} onValueChange={setTargetRole} disabled={busy}>
                <SelectTrigger id="target-role" className="w-full">
                  <SelectValue placeholder="Pick a role" />
                </SelectTrigger>
                <SelectContent>
                  {ROLE_OPTIONS.map((role) => (
                    <SelectItem key={role.value} value={role.value}>
                      {role.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="mt-1 text-xs text-muted-foreground">
                Adds a fifth expert: the Job Matcher, weighted hardest.
              </p>
            </div>
          )}

          {mode === "jd_based" && (
            <div>
              <Label htmlFor="job-description" className="mb-2 block">
                Job description
              </Label>
              <Textarea
                id="job-description"
                value={jobDescription}
                onChange={(e) =>
                  setJobDescription(e.target.value.slice(0, JD_MAX_CHARS))
                }
                disabled={busy}
                rows={6}
                placeholder="Paste the job posting here…"
              />
              <p className="mt-1 text-xs text-muted-foreground">
                {jobDescription.length}/{JD_MAX_CHARS} characters — the Job
                Matcher scores your resume against this exact posting.
              </p>
            </div>
          )}

          {mode === "custom" && (
            <div>
              <Label htmlFor="custom-instructions" className="mb-2 block">
                What should the experts focus on?
              </Label>
              <Textarea
                id="custom-instructions"
                value={customInstructions}
                onChange={(e) =>
                  setCustomInstructions(
                    e.target.value.slice(0, CUSTOM_INSTRUCTIONS_MAX_CHARS),
                  )
                }
                disabled={busy}
                rows={3}
                placeholder="e.g. Tear apart my bullet points and check my timeline math"
              />
              <p className="mt-1 text-xs text-muted-foreground">
                {customInstructions.length}/{CUSTOM_INSTRUCTIONS_MAX_CHARS}{" "}
                characters — the roast hits this hardest.
              </p>
            </div>
          )}

          {uploadError && (
            <p className="text-center text-sm text-destructive">{uploadError}</p>
          )}

          <Button
            type="submit"
            disabled={busy}
            className="w-full bg-primary shadow-lg shadow-primary/30 transition-shadow hover:shadow-primary/50"
          >
            {upload.isPending
              ? "Uploading…"
              : startAnalysis.isPending
                ? "Starting the roast…"
                : "Upload & roast"}
          </Button>
        </form>

        <UploadAside />
      </div>
    </div>
  );
}
