import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Analysis — Resume Roaster",
};

export default function AnalysisLayout({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
