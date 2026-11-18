import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Roasts — Resume Roaster",
};

export default function HistoryLayout({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
