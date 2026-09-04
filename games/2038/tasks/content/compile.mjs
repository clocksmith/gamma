import { access, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { dirname, resolve, sep } from "node:path";
import { documentSection, playerContent } from "./authored.mjs";
import { buildScenarioIndex } from "./scenario-index.mjs";
import { assertNoReferences, resolveString, resolveValue } from "./references.mjs";

const projectRoot = resolve(import.meta.dirname, "../..");
const args = process.argv.slice(2);
const checkOnly = args.includes("--check");
const validateOnly = args.includes("--validate");
const retiredRuntimeDirectory = resolve(projectRoot, "dist/runtime/generated");

function insideProject(path) {
  return path === projectRoot || path.startsWith(`${projectRoot}${sep}`);
}

function sourceRootsFor(graph) {
  const roots = graph.sourceRoots || ["content/"];
  if (!Array.isArray(roots) || roots.length === 0) {
    throw new Error("Content graph sourceRoots must be a non-empty array.");
  }
  return roots.map((sourceRoot) => {
    if (typeof sourceRoot !== "string" || !sourceRoot) {
      throw new Error(`Invalid content source root: ${sourceRoot}`);
    }
    const rootPath = resolve(projectRoot, sourceRoot);
    if (!insideProject(rootPath) || rootPath === projectRoot) {
      throw new Error(`Content source root escapes project: ${sourceRoot}`);
    }
    return { path: rootPath, directory: sourceRoot.endsWith("/") };
  });
}

function isCanonicalSource(path, sourceRoots) {
  return sourceRoots.some((sourceRoot) => sourceRoot.directory
    ? path.startsWith(`${sourceRoot.path}${sep}`) : path === sourceRoot.path);
}

async function readJson(path) {
  return JSON.parse(await readFile(path, "utf8"));
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
  const raw = playerContent(await readJson(contextPath));
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
    const resolved = resolveValue(
      playerContent(await readJson(sourcePath)),
      variables
    );
    assertNoReferences(resolved, artifact.source);
    output = `${JSON.stringify(resolved, null, 2)}\n`;
  } else if (artifact.format === "text") {
    const source = await readFile(sourcePath, "utf8");
    output = resolveString(artifact.section ? documentSection(source, artifact.section) : source, variables);
    assertNoReferences(output, artifact.source);
  } else if (artifact.format === "scenario-index") {
    output = `${JSON.stringify(await buildScenarioIndex(), null, 2)}\n`;
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
  try {
    await access(retiredRuntimeDirectory);
    stale.push("dist/runtime/generated/ (retired duplicate projection)");
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
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
  await rm(retiredRuntimeDirectory, { recursive: true, force: true });
  for (const artifact of artifacts) {
    await mkdir(dirname(artifact.targetPath), { recursive: true });
    await writeFile(artifact.targetPath, artifact.output);
  }
  process.stdout.write(
    `content-graph: generated ${artifacts.length} artifacts\n`
  );
}
