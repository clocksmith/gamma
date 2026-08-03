import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve, sep } from "node:path";
import { mergeContent } from "./merge.mjs";
import { assertNoReferences, resolveString, resolveValue } from "./references.mjs";

const projectRoot = resolve(import.meta.dirname, "../..");
const args = process.argv.slice(2);
const checkOnly = args.includes("--check");
const validateOnly = args.includes("--validate");

function insideProject(path) {
  return path === projectRoot || path.startsWith(`${projectRoot}${sep}`);
}

function sourceRootsFor(graph) {
  const roots = graph.sourceRoots || ["content/"];
  if (!Array.isArray(roots) || roots.length === 0) {
    throw new Error("Content graph sourceRoots must be a non-empty array.");
  }
  return roots.map((sourceRoot) => {
    if (typeof sourceRoot !== "string" || !sourceRoot.endsWith("/")) {
      throw new Error(`Invalid content source root: ${sourceRoot}`);
    }
    const rootPath = resolve(projectRoot, sourceRoot);
    if (!insideProject(rootPath) || rootPath === projectRoot) {
      throw new Error(`Content source root escapes project: ${sourceRoot}`);
    }
    return rootPath;
  });
}

function isCanonicalSource(path, sourceRoots) {
  return sourceRoots.some((sourceRoot) => path.startsWith(`${sourceRoot}${sep}`));
}

async function readJson(path) {
  return JSON.parse(await readFile(path, "utf8"));
}

async function readComposedJson(path, overlayPaths = []) {
  let value = await readJson(path);
  for (const overlayPath of overlayPaths) {
    const overlayDocument = await readJson(overlayPath);
    if (
      !overlayDocument ||
      typeof overlayDocument !== "object" ||
      Array.isArray(overlayDocument) ||
      !overlayDocument.content ||
      typeof overlayDocument.content !== "object" ||
      Array.isArray(overlayDocument.content)
    ) {
      throw new Error(`Content overlay must wrap an object in \"content\": ${overlayPath}`);
    }
    value = mergeContent(value, overlayDocument.content, overlayPath);
  }
  return value;
}

function resolveSourcePath(source, label, sourceRoots) {
  if (typeof source !== "string") {
    throw new Error(`Content source requires a path: ${label}`);
  }
  const path = resolve(projectRoot, source);
  if (!insideProject(path) || !isCanonicalSource(path, sourceRoots)) {
    throw new Error(`Content source must live under a graph source root: ${source}`);
  }
  return path;
}

function overlayPathsFor(descriptor, label, sourceRoots) {
  const overlays = typeof descriptor === "string" ? [] : descriptor.overlays || [];
  if (!Array.isArray(overlays)) {
    throw new Error(`Content overlays must be an array: ${label}`);
  }
  return overlays.map((overlay) => resolveSourcePath(overlay, label, sourceRoots));
}

const graphPath = resolve(projectRoot, "content/graph.json");
const graph = await readJson(graphPath);
const sourceRoots = sourceRootsFor(graph);
const variablesPath = resolve(projectRoot, graph.variables);
if (!insideProject(variablesPath) || !isCanonicalSource(variablesPath, sourceRoots)) {
  throw new Error(`Content variables must live under a graph source root: ${graph.variables}`);
}
const rawVariables = await readJson(variablesPath);
let variables = resolveValue(rawVariables, rawVariables);
assertNoReferences(variables, graph.variables);

const rawContexts = {};
for (const [name, descriptor] of Object.entries(graph.contexts || {})) {
  const path = typeof descriptor === "string" ? descriptor : descriptor.path;
  const collectionName = typeof descriptor === "string" ? undefined : descriptor.collection;
  const contextPath = resolveSourcePath(path, `context ${name}`, sourceRoots);
  const overlayPaths = overlayPathsFor(descriptor, `context ${name}`, sourceRoots);
  const raw = await readComposedJson(contextPath, overlayPaths);
  const collections = Object.values(raw).filter(Array.isArray);
  const entries = collectionName
    ? raw[collectionName]
    : collections.length === 1
      ? collections[0]
      : [];
  if (collectionName && !Array.isArray(entries)) {
    throw new Error(`Content context collection must be an array: ${name}.${collectionName}`);
  }
  rawContexts[name] = {
    ...raw,
    byId: Object.fromEntries(
      entries
        .filter((entry) => entry && typeof entry.id === "string")
        .map((entry) => [entry.id, entry])
    )
  };
}
variables = { ...variables, content: rawContexts };

const contexts = {};
for (const [name, context] of Object.entries(rawContexts)) {
  const { byId: ignoredById, ...raw } = context;
  const resolved = resolveValue(raw, variables);
  const collections = Object.values(resolved).filter(Array.isArray);
  const descriptor = graph.contexts[name];
  const collectionName = typeof descriptor === "string" ? undefined : descriptor.collection;
  const entries = collectionName
    ? resolved[collectionName]
    : collections.length === 1
      ? collections[0]
      : [];
  contexts[name] = {
    ...resolved,
    byId: Object.fromEntries(
      entries
        .filter((entry) => entry && typeof entry.id === "string")
        .map((entry) => [entry.id, entry])
    )
  };
}
variables = { ...variables, content: contexts };
assertNoReferences(variables, "content contexts");

const targets = new Set();
const artifacts = [];
for (const artifact of graph.artifacts) {
  const sourcePath = resolveSourcePath(artifact.source, artifact.target, sourceRoots);
  const targetPath = resolve(projectRoot, artifact.target);
  if (!insideProject(sourcePath) || !insideProject(targetPath)) {
    throw new Error(`Content artifact escapes project root: ${artifact.source}`);
  }
  if (targets.has(targetPath)) throw new Error(`Duplicate content target: ${artifact.target}`);
  targets.add(targetPath);

  let output;
  if (artifact.format === "json") {
    const overlayPaths = overlayPathsFor(artifact, artifact.target, sourceRoots);
    const resolved = resolveValue(
      await readComposedJson(sourcePath, overlayPaths),
      variables
    );
    assertNoReferences(resolved, artifact.source);
    output = `${JSON.stringify(resolved, null, 2)}\n`;
  } else if (artifact.format === "text") {
    if ((artifact.overlays || []).length) {
      throw new Error(`Text artifacts do not support overlays: ${artifact.target}`);
    }
    const source = await readFile(sourcePath, "utf8");
    output = resolveString(source, variables);
    assertNoReferences(output, artifact.source);
  } else {
    throw new Error(`Unsupported content format: ${artifact.format}`);
  }
  artifacts.push({ ...artifact, targetPath, output });
}

if (validateOnly) {
  process.stdout.write(
    `content-graph: validated ${artifacts.length} generated artifacts\n`
  );
} else if (checkOnly) {
  const stale = [];
  for (const artifact of artifacts) {
    let actual;
    try {
      actual = await readFile(artifact.targetPath, "utf8");
    } catch {
      stale.push(`${artifact.target} (missing)`);
      continue;
    }
    if (actual !== artifact.output) stale.push(artifact.target);
  }
  if (stale.length) {
    throw new Error(
      `Generated content drift detected:\n${stale.map((path) => `- ${path}`).join("\n")}\n` +
      "Run npm run content:build."
    );
  }
  process.stdout.write(
    `content-graph: verified ${artifacts.length} generated artifacts\n`
  );
} else {
  for (const artifact of artifacts) {
    await mkdir(dirname(artifact.targetPath), { recursive: true });
    await writeFile(artifact.targetPath, artifact.output);
  }
  process.stdout.write(
    `content-graph: generated ${artifacts.length} artifacts\n`
  );
}
