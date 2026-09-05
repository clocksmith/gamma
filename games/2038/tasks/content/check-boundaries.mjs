import { readFile, readdir } from "node:fs/promises";
import { resolve } from "node:path";
import { validateReferenceLayout } from "./authored.mjs";

const root = resolve(import.meta.dirname, "../..");
const readJson = async path => JSON.parse(await readFile(resolve(root, path), "utf8"));
const graph = await readJson("content/graph.json");
const sources = new Set(graph.artifacts.map(artifact => artifact.source));
const forbidden = new Set([
  "artDirection", "absurdity", "hiddenConsequence", "iconConcept",
  "inventoryStatus", "potentialHook", "prototypeNote", "theme", "tone"
]);

function inspect(value, path, authored) {
  if (Array.isArray(value)) return value.forEach((entry, i) => inspect(entry, `${path}/${i}`, authored));
  if (!value || typeof value !== "object") return;
  for (const [key, entry] of Object.entries(value)) {
    if (key.startsWith("$")) {
      if (!authored || !["$scenario", "$era"].includes(key)) {
        throw new Error(`Unexpected editorial metadata: ${path}/${key}`);
      }
      continue;
    }
    if (forbidden.has(key)) throw new Error(`Authoring-only field outside editorial metadata: ${path}/${key}`);
    inspect(entry, `${path}/${key}`, authored);
  }
}

let count = 0;
for (const directory of ["components", "experimental/components"]) {
  for (const file of await readdir(resolve(root, directory))) {
    if (!file.endsWith(".json")) continue;
    const path = `${directory}/${file}`;
    if (!sources.has(path)) throw new Error(`Component has no generated player projection: ${path}`);
    inspect(await readJson(path), path, true);
    count++;
  }
}
for (const artifact of graph.artifacts) {
  if ("overlays" in artifact) throw new Error(`Retired copy overlay in ${artifact.target}`);
  if (artifact.source.startsWith("content/templates/")) {
    if (artifact.layout !== true) throw new Error(`Reference must declare a layout: ${artifact.source}`);
    validateReferenceLayout(await readFile(resolve(root, artifact.source), "utf8"), artifact.source);
  }
  if (artifact.format === "json") inspect(await readJson(artifact.target), artifact.target, false);
}
for (const target of ["dist/docs/map-reference.md", "dist/docs/component-reference.md", "dist/docs/component-inventory.md"]) {
  const artifact = graph.artifacts.find(entry => entry.target === target);
  if (!artifact?.layout) throw new Error(`Missing reference projection: ${target}`);
}
for (const descriptor of Object.values(graph.contexts)) {
  if (typeof descriptor === "object" && "overlays" in descriptor) throw new Error("Retired context overlay.");
}
process.stdout.write(`content-boundaries: verified ${count} complete component sources\n`);
