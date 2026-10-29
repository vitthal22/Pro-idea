"use client";

import { motion } from "framer-motion";
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
      className={`group cursor-pointer rounded-2xl border-2 border-dashed p-10 text-center transition-all ${
        isDragActive
          ? "border-primary bg-primary/5 shadow-[0_0_40px_-12px] shadow-primary/50"
          : "border-border hover:border-primary/60 hover:bg-card"
      } ${disabled ? "cursor-not-allowed opacity-50" : ""}`}
    >
      <input {...getInputProps()} aria-label="Resume file" />
      <motion.span
        className="mx-auto mb-4 flex size-14 items-center justify-center rounded-2xl bg-primary/15 text-primary"
        animate={
          isDragActive
            ? { scale: [1, 1.12, 1], rotate: [0, -4, 4, 0] }
            : { scale: 1, rotate: 0 }
        }
        transition={
          isDragActive
            ? { repeat: Infinity, duration: 0.9, ease: "easeInOut" }
            : { duration: 0.2 }
        }
      >
        <FileUp className="size-6" />
      </motion.span>
      {isDragActive ? (
        <p className="font-medium text-primary">Drop it — let&apos;s roast</p>
      ) : (
        <>
          <p className="font-medium">
            Drag &amp; drop your resume here, or{" "}
            <span className="text-primary underline">browse</span>
          </p>
          <p className="mt-2 text-xs text-muted-foreground">
            PDF or DOCX • Max 10 MB • Roast starts automatically
          </p>
        </>
      )}
    </div>
  );
}
