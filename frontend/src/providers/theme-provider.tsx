"use client";

import { ThemeProvider as NextThemesProvider } from "next-themes";

/** Class-based theming, dark by default (the Ember design system's home). */
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="dark"
      enableSystem={false}
      disableTransitionOnChange
    >
      {children}
    </NextThemesProvider>
  );
}
