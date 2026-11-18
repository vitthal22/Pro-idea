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

const SITE_TITLE = "Resume Roaster — brutally honest AI resume feedback";
const SITE_DESCRIPTION =
  "Upload a resume and four specialised AI evaluators score it, rank every weakness, and rewrite the lines that get you screened out.";

const FALLBACK_SITE_URL = "http://localhost:3000";

/**
 * Canonical origin for metadata URLs (OG image, canonical links).
 *
 * An empty value — what hosts pass when a variable is created but left blank —
 * or one without a scheme crashes `new URL()` while Next collects page
 * metadata, which fails `next build`. `??` cannot catch either: it only
 * handles null and undefined.
 */
function resolveSiteUrl(): string {
  const configured = process.env.NEXT_PUBLIC_SITE_URL?.trim();
  if (!configured) return FALLBACK_SITE_URL;

  const candidate = /^https?:\/\//i.test(configured)
    ? configured
    : `https://${configured}`;
  try {
    return new URL(candidate).origin;
  } catch {
    console.warn(
      `[metadata] Ignoring invalid NEXT_PUBLIC_SITE_URL="${configured}" — ` +
        `using ${FALLBACK_SITE_URL}.`,
    );
    return FALLBACK_SITE_URL;
  }
}

export const metadata: Metadata = {
  metadataBase: new URL(resolveSiteUrl()),
  title: SITE_TITLE,
  description: SITE_DESCRIPTION,
  openGraph: {
    title: SITE_TITLE,
    description: SITE_DESCRIPTION,
    siteName: "Resume Roaster",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: SITE_TITLE,
    description: SITE_DESCRIPTION,
  },
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
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:rounded-md focus:border focus:border-border focus:bg-card focus:px-3 focus:py-2 focus:text-sm focus:text-foreground"
        >
          Skip to content
        </a>
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
