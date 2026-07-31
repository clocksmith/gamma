import { access, readFile } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const validScopes = new Set(["confirmed", "proposed", "all"]);

function readOptions(argv) {
  let scope = "all";
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--scope") {
      scope = argv[index + 1];
      index += 1;
    } else if (argument.startsWith("--scope=")) {
      scope = argument.split("=", 2)[1];
    } else {
      throw new Error(`Unknown migration-preflight argument: ${argument}`);
    }
  }
  if (!validScopes.has(scope)) {
    throw new Error("Use --scope=confirmed, --scope=proposed, or --scope=all.");
  }
  return { scope };
}

function literalDirectory(path) {
  return typeof path === "string"
    && path.endsWith("/")
    && !path.includes(" ")
    && !path.includes("..")
    && !path.startsWith("/");
}

function selectedGroups(map, scope) {
  return scope === "confirmed"
    ? [["confirmed", map.confirmed]]
    : scope === "proposed"
      ? [["proposed", map.proposed]]
      : [["confirmed", map.confirmed], ["proposed", map.proposed]];
}

function remapPath(path, move) {
  return path.startsWith(move.from)
    ? `${move.to}${path.slice(move.from.length)}`
    : null;
}

async function exists(path) {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

const { scope } = readOptions(process.argv.slice(2));
const map = JSON.parse(await readFile(resolve(root, "migration/path-map.json"), "utf8"));
const groups = selectedGroups(map, scope);
const blockers = [];
const moves = [];

if (map.status !== "ready_to_apply") {
  blockers.push(`Map status is ${JSON.stringify(map.status)}, not "ready_to_apply".`);
}
if (map.rules?.applyAllowed !== true) {
  blockers.push("Map rule applyAllowed is not true.");
}

for (const [group, entries] of groups) {
  if (!Array.isArray(entries)) {
    blockers.push(`Map group ${group} must be an array.`);
    continue;
  }
  for (const move of entries) {
    const executable = literalDirectory(move.from) && literalDirectory(move.to);
    const sourceExists = executable ? await exists(resolve(root, move.from)) : false;
    const destinationExists = executable ? await exists(resolve(root, move.to)) : false;
    moves.push({ group, from: move.from, to: move.to, executable, sourceExists, destinationExists });
    if (group !== "confirmed") blockers.push(`${move.from} -> ${move.to} is not approved.`);
    if (!executable) blockers.push(`${move.from} -> ${move.to} is not a literal one-source-to-one-destination mapping.`);
    if (executable && !sourceExists) blockers.push(`Source ${move.from} does not exist.`);
    if (executable && destinationExists) blockers.push(`Destination ${move.to} already exists.`);
  }
}

for (const item of map.unresolved || []) {
  blockers.push(`Unresolved decision: ${item.path} (${item.question})`);
}

const executableMoves = moves.filter((move) => move.executable);
const duplicateSources = executableMoves.filter((move, index) =>
  executableMoves.findIndex((candidate) => candidate.from === move.from) !== index
);
const duplicateDestinations = executableMoves.filter((move, index) =>
  executableMoves.findIndex((candidate) => candidate.to === move.to) !== index
);
for (const move of duplicateSources) blockers.push(`Duplicate migration source: ${move.from}.`);
for (const move of duplicateDestinations) blockers.push(`Duplicate migration destination: ${move.to}.`);
for (const move of executableMoves) {
  if (move.to.startsWith(move.from) || move.from.startsWith(move.to)) {
    blockers.push(`Source and destination overlap: ${move.from} -> ${move.to}.`);
  }
}

const graph = JSON.parse(await readFile(resolve(root, "content/graph.json"), "utf8"));
const sourceRoots = graph.sourceRoots || ["content/"];
const graphSources = [graph.variables, ...graph.artifacts.map((artifact) => artifact.source)];
const contentSourceRequirements = [];
for (const source of graphSources) {
  for (const move of executableMoves) {
    const plannedPath = remapPath(source, move);
    if (!plannedPath) continue;
    const allowedAfterMove = sourceRoots.some((sourceRoot) => plannedPath.startsWith(sourceRoot));
    contentSourceRequirements.push({ source, plannedPath, allowedAfterMove });
    if (!allowedAfterMove) {
      blockers.push(
        `Content source ${source} would move to ${plannedPath}, outside content graph sourceRoots (${sourceRoots.join(", ")}).`
      );
    }
  }
}

const report = {
  ready: blockers.length === 0,
  scope,
  mapStatus: map.status,
  activeRunGate: "Manual gate: record that simulations, playtests, renders, releases, and servers are stopped immediately before apply.",
  worktreeGate: "Record the commit and any intentionally preserved dirty paths immediately before apply; do not combine unrelated edits with the migration.",
  moves,
  contentSourceRoots: sourceRoots,
  contentSourceRequirements,
  blockers: [...new Set(blockers)]
};
process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
process.exitCode = report.ready ? 0 : 1;
