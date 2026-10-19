import { defineConfig } from "vitest/config";

// Tests run in Node unless a file asks for a DOM with
// `// @vitest-environment happy-dom`, as the card and editor tests do.
export default defineConfig({
  test: {
    include: ["tests/**/*.test.ts"],
    coverage: {
      provider: "v8",
      include: ["src/**/*.ts"],
      reporter: ["text"],
    },
  },
});
