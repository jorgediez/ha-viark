import js from "@eslint/js";
import { defineConfig } from "eslint/config";
import { configs as lit } from "eslint-plugin-lit";
import globals from "globals";
import tseslint from "typescript-eslint";

export default defineConfig(
  { ignores: ["dist/", "coverage/", "node_modules/"] },
  js.configs.recommended,
  {
    files: ["**/*.ts"],
    extends: [tseslint.configs.recommendedTypeChecked, lit["flat/recommended"]],
    languageOptions: {
      globals: globals.browser,
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
    rules: {
      // Lit calls listeners bound in templates (@click=${this._onClick}) with the
      // element as `this`, so passing a method there is not an unbound call.
      "@typescript-eslint/unbound-method": "off",
    },
  },
  {
    files: ["**/*.mjs"],
    languageOptions: { globals: globals.node },
  },
);
