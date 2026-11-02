/** Shared date formatting — one format per concept, used everywhere. */

/** "Oct 30, 2026" — card timestamps (history, resumes). */
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/** "Oct 30" — compact feeds (analytics activity). */
export function formatShortDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}
