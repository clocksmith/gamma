import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve, sep } from "node:path";

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

function lookup(root, path) {
  const segments = path.split(".").filter(Boolean);
  let value = root;
  for (const segment of segments) {
    if (
      value === null ||
      typeof value !== "object" ||
      !Object.prototype.hasOwnProperty.call(value, segment)
    ) {
      throw new Error(`Unknown content reference: \${${path}}`);
    }
    value = value[segment];
  }
  return value;
}

function parseReference(reference) {
  const [path, ...formatters] = reference.split("|").map((segment) => segment.trim());
  if (!path || formatters.some((formatter) => !formatter)) {
    throw new Error(`Invalid content reference: \${${reference}}`);
  }
  return { path, formatters };
}

function formatValue(value, formatter) {
  if (formatter !== "capitalize") {
    throw new Error(`Unknown content formatter: ${formatter}`);
  }
  if (typeof value !== "string") {
    throw new Error(`Content formatter ${formatter} requires a string value`);
  }
  const [firstCharacter = "", ...remainingCharacters] = Array.from(value);
  return `${firstCharacter.toUpperCase()}${remainingCharacters.join("")}`;
}

function resolveReference(reference, variables, stack) {
  const { path, formatters } = parseReference(reference);
  const resolved = resolveValue(lookup(variables, path), variables, [...stack, path]);
  return formatters.reduce(formatValue, resolved);
}

function resolveString(value, variables, stack = []) {
  const exact = value.match(/^\$\{([^}]+)\}$/);
  if (exact) return resolveReference(exact[1], variables, stack);
  return value.replace(/\$\{([^}]+)\}/g, (_, reference) => {
    const { path } = parseReference(reference);
    if (stack.includes(path)) {
      throw new Error(`Circular content reference: ${[...stack, path].join(" -> ")}`);
    }
    const resolved = resolveReference(reference, variables, stack);
    if (resolved === null || typeof resolved === "object") {
      throw new Error(`Embedded content reference must resolve to a scalar: \${${reference}}`);
    }
    return String(resolved);
  });
}

function resolveValue(value, variables, stack = []) {
  if (typeof value === "string") return resolveString(value, variables, stack);
  if (Array.isArray(value)) return value.map((entry) => resolveValue(entry, variables, stack));
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, entry]) => [
        resolveString(key, variables, stack),
        resolveValue(entry, variables, stack)
      ])
    );
  }
  return value;
}

function assertNoReferences(value, label) {
  const serialized = typeof value === "string" ? value : JSON.stringify(value);
  const match = serialized.match(/\$\{[^}]+\}/);
  if (match) throw new Error(`Unresolved content reference in ${label}: ${match[0]}`);
}

async function readJson(path) {
  return JSON.parse(await readFile(path, "utf8"));
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

const contexts = {};
for (const [name, descriptor] of Object.entries(graph.contexts || {})) {
  const path = typeof descriptor === "string" ? descriptor : descriptor.path;
  const collectionName = typeof descriptor === "string" ? undefined : descriptor.collection;
  if (typeof path !== "string") {
    throw new Error(`Content context requires a path: ${name}`);
  }
  const contextPath = resolve(projectRoot, path);
  if (
    !insideProject(contextPath) ||
    !isCanonicalSource(contextPath, sourceRoots)
  ) {
    throw new Error(`Content context must live under a graph source root: ${path}`);
  }
  const resolved = resolveValue(
    await readJson(contextPath),
    variables
  );
  const collections = Object.values(resolved).filter(Array.isArray);
  const entries = collectionName
    ? resolved[collectionName]
    : collections.length === 1
      ? collections[0]
      : [];
  if (collectionName && !Array.isArray(entries)) {
    throw new Error(`Content context collection must be an array: ${name}.${collectionName}`);
  }
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
  const sourcePath = resolve(projectRoot, artifact.source);
  const targetPath = resolve(projectRoot, artifact.target);
  if (!insideProject(sourcePath) || !insideProject(targetPath)) {
    throw new Error(`Content artifact escapes project root: ${artifact.source}`);
  }
  if (!isCanonicalSource(sourcePath, sourceRoots)) {
    throw new Error(`Canonical content source must live under a graph source root: ${artifact.source}`);
  }
  if (targets.has(targetPath)) throw new Error(`Duplicate content target: ${artifact.target}`);
  targets.add(targetPath);

  const source = await readFile(sourcePath, "utf8");
  let output;
  if (artifact.format === "json") {
    const resolved = resolveValue(JSON.parse(source), variables);
    assertNoReferences(resolved, artifact.source);
    output = `${JSON.stringify(resolved, null, 2)}\n`;
  } else if (artifact.format === "text") {
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
