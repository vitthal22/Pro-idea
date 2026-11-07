import { ImageResponse } from "next/og";

export const alt = "Resume Roaster: your resume, brutally roasted";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

/** Social sharing card, generated at request time so no binary asset is needed. */
export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          width: "100%",
          height: "100%",
          background: "#141110",
          color: "#f5efe8",
          padding: "72px",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "60px",
              height: "60px",
              borderRadius: "16px",
              background: "rgba(249, 124, 61, 0.18)",
              color: "#f97c3d",
              fontSize: "34px",
              fontWeight: 700,
            }}
          >
            R
          </div>
          <div style={{ display: "flex", fontSize: "30px", fontWeight: 600 }}>
            Resume Roaster
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              fontSize: "80px",
              fontWeight: 700,
              lineHeight: 1.05,
              letterSpacing: "-2px",
            }}
          >
            <div style={{ display: "flex" }}>Your resume,</div>
            <div style={{ display: "flex", color: "#f97c3d" }}>
              brutally roasted.
            </div>
          </div>
          <div style={{ display: "flex", fontSize: "30px", color: "#b8aaa0" }}>
            Four AI evaluators. One honest score. Every weakness ranked.
          </div>
        </div>

        <div
          style={{
            display: "flex",
            gap: "20px",
            fontSize: "22px",
            color: "#b8aaa0",
          }}
        >
          <div style={{ display: "flex" }}>4 evaluators</div>
          <div style={{ display: "flex" }}>8 deterministic checks</div>
          <div style={{ display: "flex" }}>50 / 50 scoring</div>
        </div>
      </div>
    ),
    size,
  );
}
