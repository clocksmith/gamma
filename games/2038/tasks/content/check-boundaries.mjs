import { readFile, readdir } from "node:fs/promises";
import { resolve } from "node:path";
import { validateReferenceLayout } from "./authored.mjs";

import { CREATIVE_FIELDS, parseComponentLore } from "./world-parser.mjs";

const root = resolve(import.meta.dirname, "../..");
const readJson = async path => JSON.parse(await readFile(resolve(root, path), "utf8"));
const graph = await readJson("content/graph.json");
const sources = new Set(graph.artifacts.map(artifact => artifact.source));
const forbidden = new Set([
  "artDirection", "absurdity", "hiddenConsequence", "iconConcept",
  "inventoryStatus", "potentialHook", "prototypeNote", "theme", "tone"
]);

const creativeFields = new Set(CREATIVE_FIELDS.values());
const lore = parseComponentLore(await readFile(resolve(root, graph.world), "utf8"));
const copyReferences = new Set();

function inspect(value, path, authored) {
  if (Array.isArray(value)) return value.forEach((entry, i) => inspect(entry, `${path}/${i}`, authored));
  if (!value || typeof value !== "object") return;
  for (const [key, entry] of Object.entries(value)) {
    if (authored && path.startsWith("components/") && creativeFields.has(key)) {
      throw new Error(`Creative prose belongs in world.md via loreRef: ${path}/${key}`);
    }
    if (key === "loreRef") {
      if (!authored || typeof entry !== "string" || !Object.hasOwn(lore, entry)) {
        throw new Error(`Unknown or uncompiled lore reference: ${path}/${key} = ${entry}`);
      }
      copyReferences.add(entry);
      continue;
    }
    if (authored && path === "components/game.json/worldEnding" && key === "$conditions") continue;
    if (key.startsWith("$")) {
      if (!authored || !["$scenario", "$era"].includes(key)) {
        throw new Error(`Unexpected editorial metadata: ${path}/${key}`);
      }
      if (key === "$scenario" && (!entry?.ref || Object.keys(entry).some(field => !["ref", "eraRelation"].includes(field)))) {
        throw new Error(`Scenario definitions belong in world.md: ${path}/${key}`);
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
for (const id of Object.keys(lore)) {
  if (!copyReferences.has(id)) throw new Error(`Unreferenced component lore: ${id}`);
}
for (const artifact of graph.artifacts) {
  if ("overlays" in artifact) throw new Error(`Retired copy overlay in ${artifact.target}`);
  if (artifact.source.startsWith("content/templates/")) {
    if (artifact.layout !== true) throw new Error(`Reference must declare a layout: ${artifact.source}`);
    validateReferenceLayout(await readFile(resolve(root, artifact.source), "utf8"), artifact.source);
  }
  if (artifact.format === "json") inspect(await readJson(artifact.target), artifact.target, false);
}
const rulebook = graph.artifacts.find(entry => entry.target === "dist/docs/core-rules.md");
if (rulebook?.source !== "rules.md" || rulebook.section || rulebook.excludeSections?.length) {
  throw new Error("The player rulebook must include all of rules.md, including map and inventory.");
}
const publicDocuments = graph.deploymentProfiles["public-playtest"].documents;
if (publicDocuments.length !== 1 || publicDocuments[0] !== "core-rules.html") {
  throw new Error("Default player documents contain one complete rulebook; supplements belong to internal review.");
}
const release = await readJson("versions/current-release.json");
const candidateDocuments = new Set(["dist/docs/core-rules.md", "physical/governance-tracks.md"]);
if (release.rulesCandidate.files.length !== candidateDocuments.size ||
    release.rulesCandidate.files.some(path => !candidateDocuments.has(path))) {
  throw new Error("The physical candidate must contain the rulebook and writable ledger, without authoring documents.");
}
for (const descriptor of Object.values(graph.contexts)) {
  if (typeof descriptor === "object" && "overlays" in descriptor) throw new Error("Retired context overlay.");
}
process.stdout.write(`content-boundaries: verified ${count} complete component sources\n`);
