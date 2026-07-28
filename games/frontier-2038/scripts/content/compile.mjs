import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve, sep } from "node:path";

const projectRoot = resolve(import.meta.dirname, "../..");
const args = process.argv.slice(2);
const checkOnly = args.includes("--check");
const validateOnly = args.includes("--validate");
const editionArg = args.find((arg) => arg.startsWith("--edition="));

function insideProject(path) {
  return path === projectRoot || path.startsWith(`${projectRoot}${sep}`);
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

function resolveString(value, variables, stack = []) {
  const exact = value.match(/^\$\{([^}]+)\}$/);
  if (exact) return resolveValue(lookup(variables, exact[1]), variables, [...stack, exact[1]]);
  return value.replace(/\$\{([^}]+)\}/g, (_, path) => {
    if (stack.includes(path)) {
      throw new Error(`Circular content reference: ${[...stack, path].join(" -> ")}`);
    }
    const resolved = resolveValue(lookup(variables, path), variables, [...stack, path]);
    if (resolved === null || typeof resolved === "object") {
      throw new Error(`Embedded content reference must resolve to a scalar: \${${path}}`);
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

function merge(left, right) {
  if (
    left && right &&
    typeof left === "object" &&
    typeof right === "object" &&
    !Array.isArray(left) &&
    !Array.isArray(right)
  ) {
    return Object.fromEntries(
      [...new Set([...Object.keys(left), ...Object.keys(right)])]
        .map((key) => [
          key,
          key in right ? merge(left[key], right[key]) : left[key]
        ])
    );
  }
  return right;
}

const graphPath = resolve(projectRoot, "content/graph.json");
const graph = await readJson(graphPath);
const edition = editionArg?.split("=", 2)[1] || graph.defaultEdition;
if (!graph.editions?.[edition]) throw new Error(`Unknown content edition: ${edition}`);
const variablesPath = resolve(projectRoot, graph.variables);
const rawVariables = await readJson(variablesPath);
const editionVariables = await readJson(resolve(projectRoot, graph.editions[edition]));
const mergedVariables = merge(rawVariables, editionVariables);
let variables = resolveValue(mergedVariables, mergedVariables);
assertNoReferences(variables, graph.variables);

const contexts = {};
for (const [name, path] of Object.entries(graph.contexts || {})) {
  const contextPath = resolve(projectRoot, path);
  if (
    !insideProject(contextPath) ||
    !contextPath.startsWith(resolve(projectRoot, "content") + sep)
  ) {
    throw new Error(`Content context must live under content/: ${path}`);
  }
  const resolved = resolveValue(
    await readJson(contextPath),
    variables
  );
  const collections = Object.values(resolved).filter(Array.isArray);
  const entries = collections.length === 1 ? collections[0] : [];
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
  if (!sourcePath.startsWith(resolve(projectRoot, "content") + sep)) {
    throw new Error(`Canonical content source must live under content/: ${artifact.source}`);
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
    `content-graph: validated ${artifacts.length} generated artifacts for ${edition} edition\n`
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
    `content-graph: verified ${artifacts.length} generated artifacts for ${edition} edition\n`
  );
} else {
  for (const artifact of artifacts) {
    await mkdir(dirname(artifact.targetPath), { recursive: true });
    await writeFile(artifact.targetPath, artifact.output);
  }
  process.stdout.write(
    `content-graph: generated ${artifacts.length} artifacts for ${edition} edition\n`
  );
}
