import { Toaster } from "@/components/ui/sonner";

import { AppProviders } from "@/providers/app-providers";
import { ThemeProvider } from "@/providers/theme-provider";

import type { Metadata } from "next";
import { Bricolage_Grotesque, Instrument_Sans, Spline_Sans_Mono } from "next/font/google";
import "./globals.css";

const display = Bricolage_Grotesque({
  variable: "--font-display",
  subsets: ["latin"],
});

const sans = Instrument_Sans({
  variable: "--font-sans",
  subsets: ["latin"],
});

const mono = Spline_Sans_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Resume Roaster — brutally honest AI resume feedback",
  description:
    "AI-powered resume analysis with a multi-evaluator pipeline that delivers brutally honest, constructive feedback.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      // next-themes sets the class before hydration; without this React
      // warns about the mismatch it created on purpose.
      suppressHydrationWarning
      className={`${display.variable} ${sans.variable} ${mono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <ThemeProvider>
          <AppProviders>
            {children}
            <Toaster />
          </AppProviders>
        </ThemeProvider>
      </body>
    </html>
  );
}
