"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ResumeDropzone } from "@/components/upload/ResumeDropzone";
import { useUploadResume } from "@/hooks/mutations/use-upload";
import { useStartAnalysis } from "@/hooks/mutations/use-start-analysis";
import { useCurrentUser } from "@/hooks/queries/use-auth";
import { Sidebar } from "@/components/layout/Sidebar";
import { useAuthStore } from "@/stores/auth-store";

export default function UploadPage() {
  const { isPending, isError, error } = useCurrentUser();
  const { token } = useAuthStore((s) => s);
  const router = useRouter();
  const upload = useUploadResume();
  const startAnalysis = useStartAnalysis();

  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);

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
    // Auto-roast: the roast starts as soon as the upload succeeds.
    upload.mutate(file, {
      onSuccess: (resume) => {
        startAnalysis.mutate(
          { resumeId: resume.id },
          {
            onSuccess: (created) =>
              router.push(`/analysis/${created.analysis_id}`),
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
      <div className="flex min-h-screen items-center justify-center bg-background p-6">
        <div className="w-full max-w-md rounded-2xl border border-border bg-card p-8 text-center">
          <p className="font-medium">
            Please{" "}
            <a href="/login" className="font-medium underline">
              log in
            </a>{" "}
            to upload
          </p>
        </div>
      </div>
    );
  }

  if (isPending) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background p-6">
        <div className="rounded-2xl border border-border bg-card p-8 text-center">
          <p className="font-medium">Loading…</p>
          <Skeleton className="mt-4 h-6 w-48" />
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background p-6">
        <div className="w-full max-w-md rounded-2xl border border-border bg-card p-8 text-center">
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
      </div>
    );
  }

  const uploadError =
    fileError ??
    (upload.error instanceof Error ? upload.error.message : null);
  const busy = upload.isPending || startAnalysis.isPending;

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />

      <div className="flex-1 p-6 md:p-8">
        <div className="mx-auto max-w-xl py-10">
          <h2 className="mb-2 text-center text-2xl font-bold">
            Upload Resume
          </h2>
          <p className="mb-6 text-center text-sm text-muted-foreground">
            Your roast starts automatically — four experts, one brutal score.
          </p>

          <form onSubmit={handleSubmit} className="space-y-6">
            <ResumeDropzone
              onFileSelected={handleFileSelected}
              onFileError={handleFileError}
              disabled={busy}
            />

            {file && (
              <p className="text-center text-sm text-primary">
                Selected: {file.name} ({Math.round(file.size / 1024)} KB)
              </p>
            )}

            {uploadError && (
              <p className="text-center text-sm text-destructive">
                {uploadError}
              </p>
            )}

            <Button
              type="submit"
              disabled={busy}
              className="w-full"
            >
              {upload.isPending
                ? "Uploading…"
                : startAnalysis.isPending
                  ? "Starting the roast…"
                  : "Upload & roast"}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
