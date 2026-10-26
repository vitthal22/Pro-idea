import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {
    // The repo root holds the root package.json/lockfile — silence the
    // "multiple lockfiles" warning when running from the root.
    root: path.join(__dirname, ".."),
  },
};

export default nextConfig;
