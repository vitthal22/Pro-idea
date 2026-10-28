"use client";

import { FileUp } from "lucide-react";
import { useCallback } from "react";
import { useDropzone, type FileRejection } from "react-dropzone";

// Client-side validation only — the backend re-validates type and size
// from the actual file content.
const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024;

const ACCEPTED_TYPES = {
  "application/pdf": [".pdf"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
    ".docx",
  ],
};

interface ResumeDropzoneProps {
  onFileSelected: (file: File) => void;
  onFileError: (message: string) => void;
  disabled?: boolean;
}

function rejectionMessage(rejections: FileRejection[]): string {
  const codes = rejections[0]?.errors.map((e) => e.code) ?? [];
  if (codes.includes("file-too-large")) {
    return "That file is larger than 10 MB.";
  }
  if (codes.includes("file-invalid-type")) {
    return "Only PDF and DOCX files are supported.";
  }
  return "That file cannot be uploaded.";
}

export function ResumeDropzone({
  onFileSelected,
  onFileError,
  disabled = false,
}: ResumeDropzoneProps) {
  const onDrop = useCallback(
    (accepted: File[], rejections: FileRejection[]) => {
      if (rejections.length > 0) {
        onFileError(rejectionMessage(rejections));
        return;
      }
      if (accepted.length > 0) {
        onFileError("");
        onFileSelected(accepted[0]);
      }
    },
    [onFileError, onFileSelected],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: MAX_FILE_SIZE_BYTES,
    multiple: false,
    disabled,
  });

  return (
    <div
      {...getRootProps()}
      className={`cursor-pointer rounded-2xl border-2 border-dashed p-12 text-center transition-colors ${
        isDragActive
          ? "border-primary bg-primary/5"
          : "border-border hover:border-primary"
      } ${disabled ? "cursor-not-allowed opacity-50" : ""}`}
    >
      <input {...getInputProps()} aria-label="Resume file" />
      <FileUp className="mx-auto mb-2 size-6 text-muted-foreground" />
      {isDragActive ? (
        <span className="block text-muted-foreground">Drop the file here…</span>
      ) : (
        <>
          <span className="block text-muted-foreground">
            Drag &amp; drop a file here, or click to choose
          </span>
          <span className="mt-1 block text-xs text-muted-foreground">
            PDF or DOCX • Max 10 MB
          </span>
        </>
      )}
    </div>
  );
}
