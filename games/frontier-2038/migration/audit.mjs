import { readFile, readdir } from "node:fs/promises";
import { resolve, relative, sep } from "node:path";

const root = resolve(import.meta.dirname, "..");
const validScopes = new Set(["confirmed", "proposed", "all"]);

function readOptions(argv) {
  let scope = "confirmed";
  let includeArchive = false;
  let includePreservedReferences = false;
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--include-archive") {
      includeArchive = true;
    } else if (argument === "--include-preserved-references") {
      includePreservedReferences = true;
    } else if (argument === "--scope") {
      scope = argv[index + 1];
      index += 1;
    } else if (argument.startsWith("--scope=")) {
      scope = argument.split("=", 2)[1];
    } else {
      throw new Error(`Unknown migration-audit argument: ${argument}`);
    }
  }
  if (!validScopes.has(scope)) {
    throw new Error("Use --scope=confirmed, --scope=proposed, or --scope=all.");
  }
  return { scope, includeArchive, includePreservedReferences };
}

function literalDirectory(path) {
  return typeof path === "string"
    && path.endsWith("/")
    && !path.includes(" ")
    && !path.includes("..")
    && !path.startsWith("/");
}

function selectedMoves(map, scope) {
  return [
    ...(scope === "proposed" ? [] : map.confirmed),
    ...(scope === "confirmed" ? [] : map.proposed)
  ];
}

const { scope, includeArchive, includePreservedReferences } = readOptions(process.argv.slice(2));
const map = JSON.parse(await readFile(resolve(root, "migration/path-map.json"), "utf8"));
const contentGraph = JSON.parse(await readFile(resolve(root, "content/graph.json"), "utf8"));
const generatedTargets = new Set((contentGraph.artifacts || []).map((artifact) => artifact.target));
const audits = selectedMoves(map, scope).map((move) => ({
  ...move,
  auditable: literalDirectory(move.from),
  liveReferences: [],
  preservedReferenceSummary: {
    generated: 0,
    evidence: 0,
    archive: 0
  },
  preservedReferences: includePreservedReferences
    ? { generated: [], evidence: [], archive: [] }
    : undefined
}));
const skippedDirectories = new Set([".git", "node_modules", "migration"]);
if (!includeArchive) skippedDirectories.add("versions");

async function trackedTextFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const path = resolve(directory, entry.name);
    const repoPath = relative(root, path).split(sep).join("/");
    if (entry.isDirectory()) {
      if (!skippedDirectories.has(entry.name)) files.push(...await trackedTextFiles(path));
      continue;
    }
    if (entry.isFile()) files.push(path);
  }
  return files;
}

function referenceClass(repoPath) {
  if (repoPath.startsWith("dist/") || generatedTargets.has(repoPath)) return "generated";
  if (repoPath.startsWith("studies/") || repoPath.startsWith("playtests/")) return "evidence";
  if (repoPath.startsWith("versions/")) return "archive";
  return "live";
}

for (const file of await trackedTextFiles(root)) {
  const repoPath = relative(root, file).split(sep).join("/");
  let text;
  try {
    text = await readFile(file, "utf8");
  } catch {
    continue;
  }
  for (const audit of audits) {
    if (!audit.auditable) continue;
    const barePath = audit.from.slice(0, -1);
    if (text.includes(audit.from) || text.includes(barePath)) {
      const category = referenceClass(repoPath);
      if (category === "live") {
        audit.liveReferences.push(repoPath);
      } else {
        audit.preservedReferenceSummary[category] += 1;
        if (includePreservedReferences) audit.preservedReferences[category].push(repoPath);
      }
    }
  }
}

for (const audit of audits) {
  audit.liveReferences = [...new Set(audit.liveReferences)].sort();
  if (audit.preservedReferences) {
    for (const category of Object.keys(audit.preservedReferences)) {
      audit.preservedReferences[category] = [...new Set(audit.preservedReferences[category])].sort();
    }
  }
}

const report = {
  status: map.status,
  scope,
  includeArchive,
  includePreservedReferences,
  archivePolicy: map.rules?.archivePolicy,
  moves: audits,
  blockers: audits
    .filter((audit) => !audit.auditable)
    .map((audit) => `${audit.from} is not a literal one-source directory mapping.`)
};
process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
