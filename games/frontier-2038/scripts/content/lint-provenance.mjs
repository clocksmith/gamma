import { access, readFile } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "../..");
const registryPath = resolve(root, "content/provenance/numbers.json");
const registry = JSON.parse(await readFile(registryPath, "utf8"));
const ignored = new Set(registry.nonBalanceKeys || []);
let hypotheses = 0;
let evidence = 0;

function visit(value, path, document) {
  if (typeof value === "number") {
    const key = path.at(-1);
    if (ignored.has(key)) return;
    const pointer = `/${path.join("/")}`;
    const override = document.evidenceOverrides?.[pointer];
    const status = override || document.default;
    if (status === "hypothesis") hypotheses += 1;
    else if (typeof status === "string" && status.startsWith("evidence:")) evidence += 1;
    else throw new Error(`Invalid numeric provenance at ${pointer}: ${status}`);
    return;
  }
  if (Array.isArray(value)) {
    value.forEach((entry, index) => visit(entry, [...path, String(index)], document));
    return;
  }
  if (value && typeof value === "object") {
    for (const [key, entry] of Object.entries(value)) {
      visit(entry, [...path, key], document);
    }
  }
}

for (const [relative, document] of Object.entries(registry.documents)) {
  if (!["hypothesis"].includes(document.default) &&
      !String(document.default).startsWith("evidence:")) {
    throw new Error(`Invalid default numeric provenance for ${relative}.`);
  }
  const contents = await readFile(resolve(root, relative), "utf8");
  const parsed = JSON.parse(contents);
  visit(parsed, [], document);
  for (const receipt of Object.values(document.evidenceOverrides || {})) {
    if (!String(receipt).startsWith("evidence:")) {
      throw new Error(`Evidence override in ${relative} must use evidence:<receipt-id>.`);
    }
    const receiptId = String(receipt).slice("evidence:".length);
    await access(resolve(root, "studies/simulation", `${receiptId}.md`));
  }
  const suspect = [];
  const inspect = (value) => {
    if (typeof value === "string" &&
        /\b(?:tested|balanced|validated)\b/i.test(value) &&
        /\d/.test(value)) suspect.push(value);
    else if (Array.isArray(value)) value.forEach(inspect);
    else if (value && typeof value === "object") Object.values(value).forEach(inspect);
  };
  inspect(parsed);
  if (suspect.length) {
    throw new Error(
      `${relative} claims a numbered value is tested/balanced/validated while its ` +
      `provenance defaults to hypothesis: ${suspect[0]}`
    );
  }
}

if (hypotheses + evidence === 0) throw new Error("Numeric provenance registry covers no values.");
process.stdout.write(
  `numeric-provenance: ${hypotheses} hypotheses, ${evidence} evidence-backed values\n`
);
