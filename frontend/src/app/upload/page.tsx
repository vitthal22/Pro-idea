"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ResumeDropzone } from "@/components/upload/ResumeDropzone";
import { useUploadResume } from "@/hooks/mutations/use-upload";
import { useCurrentUser } from "@/hooks/queries/use-auth";
import { Sidebar } from "@/components/layout/Sidebar";
import { useAuthStore } from "@/stores/auth-store";

export default function UploadPage() {
  const { isPending, isError, error } = useCurrentUser();
  const { token } = useAuthStore((s) => s);
  const router = useRouter();
  const upload = useUploadResume();

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
    upload.mutate(file, { onSuccess: () => router.push("/dashboard") });
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

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />

      <div className="flex-1 p-6 md:p-8">
        <div className="mx-auto max-w-xl py-10">
          <h2 className="mb-6 text-center text-2xl font-bold">
            Upload Resume
          </h2>

          <form onSubmit={handleSubmit} className="space-y-6">
            <ResumeDropzone
              onFileSelected={handleFileSelected}
              onFileError={handleFileError}
              disabled={upload.isPending}
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
              disabled={upload.isPending}
              className="w-full"
            >
              {upload.isPending ? "Uploading…" : "Upload Resume"}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
