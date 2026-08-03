import { readFile, readdir } from "node:fs/promises";
import { relative, resolve, sep } from "node:path";

const root = resolve(import.meta.dirname, "../..");
const graph = JSON.parse(
  await readFile(resolve(root, "content/graph.json"), "utf8")
);

const nonPlayerFields = new Set([
  "artDirection",
  "absurdity",
  "hiddenConsequence",
  "iconConcept",
  "inventoryStatus",
  "potentialHook",
  "prototypeNote",
  "theme",
  "tone"
]);

function collectFields(value, trail = [], matches = []) {
  if (Array.isArray(value)) {
    value.forEach((entry, index) => collectFields(entry, [...trail, String(index)], matches));
    return matches;
  }
  if (!value || typeof value !== "object") return matches;
  for (const [key, entry] of Object.entries(value)) {
    const path = [...trail, key];
    if (nonPlayerFields.has(key)) matches.push(path.join("."));
    collectFields(entry, path, matches);
  }
  return matches;
}

function collectLeaves(value, trail = [], leaves = []) {
  if (Array.isArray(value)) {
    if (value.every((entry) => !entry || typeof entry !== "object")) {
      leaves.push(`${trail.join(".")}[]`);
    } else {
      value.forEach((entry) => collectLeaves(entry, [...trail.slice(0, -1), `${trail.at(-1)}[]`], leaves));
    }
    return leaves;
  }
  if (!value || typeof value !== "object") {
    leaves.push(trail.join("."));
    return leaves;
  }
  for (const [key, entry] of Object.entries(value)) {
    if (key === "id" || key === "factionId") continue;
    collectLeaves(entry, [...trail, key], leaves);
  }
  return leaves;
}

function prefixOwns(prefix, path) {
  return path === prefix || path.startsWith(`${prefix}.`) || path.startsWith(`${prefix}[]`);
}

async function readJson(path) {
  return JSON.parse(await readFile(resolve(root, path), "utf8"));
}

function assertWrapper(document, path) {
  const keys = Object.keys(document).sort();
  if (keys.join(",") !== "content,schemaVersion") {
    throw new Error(`${path} must contain only schemaVersion and content`);
  }
  if (document.schemaVersion !== 1) {
    throw new Error(`${path} must use schemaVersion 1`);
  }
  if (!document.content || typeof document.content !== "object" || Array.isArray(document.content)) {
    throw new Error(`${path} must wrap an object in content`);
  }
}

async function walk(directory) {
  const paths = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = resolve(directory, entry.name);
    if (entry.isDirectory()) paths.push(...await walk(path));
    else if (entry.isFile() && entry.name.endsWith(".json")) paths.push(path);
  }
  return paths;
}

const artifactOverlays = new Set(
  graph.artifacts.flatMap((artifact) => artifact.overlays || [])
);
const contextOverlays = new Set(
  Object.values(graph.contexts || {}).flatMap((descriptor) =>
    typeof descriptor === "string" ? [] : descriptor.overlays || []
  )
);
const projectedSources = new Set([
  ...graph.artifacts.map((artifact) => artifact.source),
  ...artifactOverlays,
  ...Object.values(graph.contexts || {}).map((descriptor) =>
    typeof descriptor === "string" ? descriptor : descriptor.path
  ),
  ...contextOverlays
]);

const copyDirectories = ["content/copy", "experimental/copy"];
const copyFiles = (await Promise.all(copyDirectories.map(async (directory) =>
  (await walk(resolve(root, directory))).map((path) => relative(root, path).split(sep).join("/"))
))).flat();
const copyContract = await readJson(graph.playerCopyContract);
if (copyContract.schemaVersion !== 1 || !copyContract.sources) {
  throw new Error(`${graph.playerCopyContract} must declare schemaVersion 1 sources`);
}
const contractedCopyFiles = new Set(Object.keys(copyContract.sources));
for (const path of copyFiles) {
  if (!artifactOverlays.has(path)) {
    throw new Error(`Player-copy source has no generated player projection: ${path}`);
  }
  const document = await readJson(path);
  assertWrapper(document, path);
  const leaked = collectFields(document.content);
  if (leaked.length) {
    throw new Error(`Authoring-only fields in ${path}: ${leaked.join(", ")}`);
  }
  const mappings = copyContract.sources[path];
  if (!Array.isArray(mappings) || !mappings.length) {
    throw new Error(`Player-copy source lacks a surface contract: ${path}`);
  }
  const leaves = collectLeaves(document.content);
  for (const leaf of leaves) {
    if (!mappings.some(({ prefix }) => prefixOwns(prefix, leaf))) {
      throw new Error(`Player-copy field lacks a declared player surface: ${path}#${leaf}`);
    }
  }
  for (const mapping of mappings) {
    if (
      typeof mapping.prefix !== "string" ||
      !Array.isArray(mapping.surfaces) ||
      !mapping.surfaces.length ||
      !mapping.surfaces.every((surface) => typeof surface === "string" && surface.trim())
    ) {
      throw new Error(`Invalid player-copy surface mapping in ${path}`);
    }
    if (!leaves.some((leaf) => prefixOwns(mapping.prefix, leaf))) {
      throw new Error(`Unused player-copy surface mapping: ${path}#${mapping.prefix}`);
    }
  }
}
for (const path of contractedCopyFiles) {
  if (!copyFiles.includes(path)) throw new Error(`Missing contracted player-copy source: ${path}`);
}

for (const path of artifactOverlays) {
  if (!path.startsWith("content/copy/") && !path.startsWith("experimental/copy/")) {
    throw new Error(`Generated overlay is not a player-copy source: ${path}`);
  }
}

for (const artifact of graph.artifacts.filter((entry) => entry.overlays?.length)) {
  const mechanics = await readJson(artifact.source);
  const leaked = collectFields(mechanics);
  if (leaked.length) {
    throw new Error(`Authoring-only fields in mechanics ${artifact.source}: ${leaked.join(", ")}`);
  }
  const generated = await readJson(artifact.target);
  const generatedLeak = collectFields(generated);
  if (generatedLeak.length) {
    throw new Error(`Authoring-only fields in ${artifact.target}: ${generatedLeak.join(", ")}`);
  }
}

process.stdout.write(
  `content-boundaries: verified ${copyFiles.length} surface-bound player-copy sources\n`
);
