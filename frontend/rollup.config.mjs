import nodeResolve from "@rollup/plugin-node-resolve";
import terser from "@rollup/plugin-terser";
import typescript from "@rollup/plugin-typescript";

const dev = process.env.ROLLUP_WATCH === "true";

export default {
  input: "src/viark-remote-card.ts",
  output: {
    file: "dist/ha-viark-remote-card.js",
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
