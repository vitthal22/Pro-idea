"use client";

import { useEffect, useRef, useState } from "react";

/** Gap between two words lighting up, in milliseconds. */
const WORD_STAGGER_MS = 55;

/**
 * The one large type moment on the page: every word starts muted and lights up
 * in reading order once the block enters the viewport. Under reduced motion the
 * text is shown at full colour immediately.
 */
export function TaglineReveal({ lines }: { lines: string[] }) {
  const ref = useRef<HTMLParagraphElement>(null);
  const [active, setActive] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    // Without IntersectionObserver (very old browsers) reveal on the next
    // frame instead of leaving the text muted forever.
    if (typeof IntersectionObserver === "undefined") {
      const frame = requestAnimationFrame(() => setActive(true));
      return () => cancelAnimationFrame(frame);
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setActive(true);
          observer.disconnect();
        }
      },
      { threshold: 0.35 },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  // Flatten once with an absolute index so each word knows its own delay.
  const words = lines
    .flatMap((line, lineIndex) =>
      line.split(" ").map((word) => ({ word, lineIndex })),
    )
    .map((token, index) => ({ ...token, index }));

  return (
    <p ref={ref} className="max-w-[680px] heading-3 text-balance sm:heading-2">
      {lines.map((line, lineIndex) => (
        <span key={line} className="block">
          {words
            .filter((token) => token.lineIndex === lineIndex)
            .map((token) => (
              <span
                key={`${token.word}-${token.index}`}
                style={{ transitionDelay: `${token.index * WORD_STAGGER_MS}ms` }}
                className={`inline-block transition-opacity duration-700 ease-[cubic-bezier(0.22,1,0.36,1)] motion-reduce:opacity-100 motion-reduce:transition-none ${
                  active ? "opacity-100" : "opacity-30"
                }`}
              >
                {token.word}
                {"\u00A0"}
              </span>
            ))}
        </span>
      ))}
    </p>
  );
}
