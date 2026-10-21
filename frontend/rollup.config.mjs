import nodeResolve from "@rollup/plugin-node-resolve";
import terser from "@rollup/plugin-terser";
import typescript from "@rollup/plugin-typescript";

const dev = process.env.ROLLUP_WATCH === "true";

// The card ships inside the integration: Home Assistant serves this file, and
// CI checks the committed copy matches a fresh build.
export default {
  input: "src/viark-remote-card.ts",
  output: {
    file: "../custom_components/viark/www/viark-remote-card.js",
    format: "es",
    sourcemap: dev,
    inlineDynamicImports: true,
  },
  plugins: [
    nodeResolve(),
    typescript({ include: ["src/**/*.ts"], noEmitOnError: true }),
    !dev && terser({ format: { comments: false } }),
  ],
};
