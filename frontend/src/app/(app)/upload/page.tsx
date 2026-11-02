"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { FileText, X } from "lucide-react";
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
  "cursor-pointer rounded-xl border p-3 text-left transition-colors has-[[data-state=checked]]:border-primary has-[[data-state=checked]]:bg-primary/10";

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
      <div className="mx-auto max-w-md rounded-2xl border border-border bg-card p-8 text-center">
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
      <div className="mx-auto max-w-md rounded-2xl border border-border bg-card p-8 text-center">
        <p className="font-medium">Loading…</p>
        <Skeleton className="mt-4 h-6 w-48" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="mx-auto max-w-md rounded-2xl border border-border bg-card p-8 text-center">
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
    <div>
      <PageHeader
        title="Upload Resume"
        description="Pick how hard to roast, drop the file — the experts start automatically."
      />

      <form onSubmit={handleSubmit} className="space-y-6">
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
          <div className="grid grid-cols-2 gap-2">
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
          className="w-full bg-gradient-to-r from-primary to-amber-500 shadow-lg shadow-primary/30 transition-shadow hover:shadow-primary/50"
        >
          {upload.isPending
            ? "Uploading…"
            : startAnalysis.isPending
              ? "Starting the roast…"
              : "Upload & roast"}
        </Button>
      </form>
    </div>
  );
}
