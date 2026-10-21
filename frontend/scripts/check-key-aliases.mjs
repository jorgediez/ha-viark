// Compares the card's copy of the integration's key names
// (tests/integration-key-aliases.json) with KEY_ALIASES in the integration's
// const.py, in this repository.
//
//   node scripts/check-key-aliases.mjs
//
// The card sends keys by name, so a name the integration drops breaks a button,
// and a name it adds may be one the card can now map. Either way the copy needs
// updating, so any difference fails.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const copy = JSON.parse(
  readFileSync(resolve(root, "tests/integration-key-aliases.json"), "utf8"),
);
const constPy = readFileSync(
  resolve(root, "../custom_components/viark/const.py"),
  "utf8",
);

/** The names in `KEY_ALIASES = { ... }`, including the generated digit_0..9. */
function keyAliases(text) {
  const start = text.search(/^KEY_ALIASES\b/m);
  const end = text.indexOf("\n}", start);
  if (start < 0 || end < 0) {
    throw new Error("KEY_ALIASES not found in const.py");
  }
  const block = text.slice(start, end);
  const names = [...block.matchAll(/^\s+"([a-z0-9_]+)":/gm)].map((m) => m[1]);
  if (/f"digit_\{\w+\}"/.test(block)) {
    names.push(...Array.from({ length: 10 }, (_, d) => `digit_${d}`));
  }
  // A table this small means the format changed, not the keys.
  if (names.length < 20) {
    throw new Error(`Found only ${names.length} names; has KEY_ALIASES changed shape?`);
  }
  return new Set(names);
}

const upstream = keyAliases(constPy);
const ours = new Set(copy.keys);
const added = [...upstream].filter((k) => !ours.has(k)).sort();
const removed = [...ours].filter((k) => !upstream.has(k)).sort();

if (added.length === 0 && removed.length === 0) {
  console.log(`In step: ${ours.size} key names match the integration's KEY_ALIASES.`);
  process.exit(0);
}
if (removed.length) {
  console.error(
    `Removed from const.py, but still in the card's copy: ${removed.join(", ")}.\n` +
      "Any button that sends one of these is broken; remap it before releasing.",
  );
}
if (added.length) {
  console.error(
    `Added to const.py, missing from the card's copy: ${added.join(", ")}.\n` +
      "A button marked unsupported may now have a key.",
  );
}
console.error("Update tests/integration-key-aliases.json to match.");
process.exit(1);
