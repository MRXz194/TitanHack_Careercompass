import react from "@vitejs/plugin-react";
import path from "node:path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname) },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    include: ["tests/**/*.test.{ts,tsx}"],
    // transparency-copy.test.ts (PR-09/M6) is a standalone `assert` script meant to
    // run via `npx tsx`, not a vitest suite — see docs/handoffs/M4_PR-09_TRANSPARENCY_COPY_HANDOFF.md.
    exclude: ["**/node_modules/**", "**/transparency-copy.test.ts"],
  },
});
