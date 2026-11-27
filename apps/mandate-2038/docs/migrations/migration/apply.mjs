import { execFile } from "node:child_process";
import { access, mkdir, readFile, rename, stat, writeFile } from "node:fs/promises";
import { dirname, relative, resolve, sep } from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const root = resolve(import.meta.dirname, "..");
const map = JSON.parse(await readFile(resolve(root, "migration/path-map.json"), "utf8"));
const acknowledgement = process.argv.find((argument) => argument.startsWith("--acknowledge-stopped-services="));

if (!acknowledgement) {
  throw new Error("Refusing migration without --acknowledge-stopped-services=<recorded-check>.");
}
if (map.status !== "ready_to_apply" || map.rules?.applyAllowed !== true || map.unresolved?.length) {
  throw new Error("Migration map is not approved for application.");
}

const moves = map.confirmed;
const preservedRoots = ["migration/", "versions/", "evidence/", "studies/", "playtests/", "build/", "dist/"];

async function exists(path) {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

async function trackedFiles() {
  const { stdout } = await execFileAsync("git", ["ls-files", "-z"], { cwd: root, maxBuffer: 32 * 1024 * 1024 });
  return stdout.split("\0").filter(Boolean);
}

function replacementPairs() {
  return [...moves]
    .sort((left, right) => right.from.length - left.from.length)
    .map((move) => [move.from, move.to]);
}

async function rewriteLiveReferences() {
  const replacements = replacementPairs();
  for (const repoPath of await trackedFiles()) {
    if (preservedRoots.some((rootPath) => repoPath.startsWith(rootPath))) continue;
    const path = resolve(root, repoPath);
    let source;
    try {
      source = await readFile(path, "utf8");
    } catch {
      continue;
    }
    const rewritten = replacements.reduce(
      (text, [from, to]) => text.replaceAll(from, to),
      source
    );
    if (rewritten !== source) await writeFile(path, rewritten);
  }
}

async function move(entry) {
  const from = resolve(root, entry.from);
  const to = resolve(root, entry.to);
  if (!await exists(from)) throw new Error(`Missing migration source: ${entry.from}`);
  if (await exists(to)) throw new Error(`Migration destination already exists: ${entry.to}`);
  await mkdir(dirname(to), { recursive: true });
  await rename(from, to);
  const moved = await stat(to);
  if (!moved.isDirectory() && entry.from.endsWith("/")) {
    throw new Error(`Expected directory migration target: ${entry.to}`);
  }
}

await rewriteLiveReferences();

const graphPath = resolve(root, "content/graph.json");
const graph = JSON.parse(await readFile(graphPath, "utf8"));
graph.sourceRoots = ["content/", "physical/", "web/"];
await writeFile(graphPath, `${JSON.stringify(graph, null, 2)}\n`);

for (const entry of moves) await move(entry);

const receipt = {
  schemaVersion: 1,
  migration: "2026-07-31-layout",
  acknowledgement: acknowledgement.split("=", 2)[1],
  moves: moves.map(({ from, to }) => ({ from, to })),
  preservedRoots,
  next: ["npm run build:all", "npm run game:release", "npm test", "npm run check"]
};
const receiptPath = resolve(root, "migration/receipts/2026-07-31-layout/apply.json");
await mkdir(dirname(receiptPath), { recursive: true });
await writeFile(receiptPath, `${JSON.stringify(receipt, null, 2)}\n`);
process.stdout.write(`migration: moved ${moves.length} sources; rebuild generated outputs next\n`);
