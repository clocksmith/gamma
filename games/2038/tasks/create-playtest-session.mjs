import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const projectRoot = resolve(import.meta.dirname, "..");
const execFileAsync = promisify(execFile);

function argumentsFrom(values) {
  const result = {};
  for (let index = 0; index < values.length; index += 1) {
    const key = values[index];
    if (!key.startsWith("--")) throw new TypeError(`Unexpected argument: ${key}`);
    const value = values[index + 1];
    if (!value || value.startsWith("--")) throw new TypeError(`Missing value for ${key}`);
    result[key.slice(2)] = value;
    index += 1;
  }
  return result;
}

function slug(value) {
  return String(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 48);
}

const input = argumentsFrom(process.argv.slice(2));
const playerCount = Number(input.players || 4);
if (!Number.isInteger(playerCount) || playerCount < 3 || playerCount > 5) {
  throw new RangeError("--players must be an integer from 3 to 5.");
}
const evidenceType = input.type || "facilitated_playtest";
if (!["facilitated_playtest", "blind_playtest"].includes(evidenceType)) {
  throw new TypeError("--type must be facilitated_playtest or blind_playtest.");
}
const boardSeed = String(input.seed || "frontier-playtest");
const playedAt = new Date().toISOString();
const date = input.date || playedAt.slice(0, 10);
if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
  throw new TypeError("--date must use YYYY-MM-DD.");
}

const current = JSON.parse(
  await readFile(resolve(projectRoot, "versions/current.json"), "utf8")
);
const { stdout: sourceCommitOutput } = await execFileAsync(
  "git",
  ["rev-parse", "HEAD"],
  { cwd: projectRoot }
);
const sourceCommit = sourceCommitOutput.trim();
const selectedRelease = current.rulesCandidate || current;
const kitManifestPath = input["kit-manifest"]
  ? resolve(input["kit-manifest"])
  : resolve(projectRoot, "dist/physical-kit/current.json");
let physicalKitManifest;
try {
  physicalKitManifest = JSON.parse(await readFile(kitManifestPath, "utf8"));
} catch {
  throw new Error(
    "No frozen physical-kit identity is available. Run npm run physical-kit:freeze first."
  );
}
if (
  physicalKitManifest.identity?.sourceCommit !== sourceCommit ||
  physicalKitManifest.identity?.rulesVersion !== selectedRelease.version ||
  physicalKitManifest.identity?.executableVersion !== current.gameVersion
) {
  throw new Error(
    "Frozen physical-kit identity does not match this source and release. Run npm run physical-kit:freeze."
  );
}
const manifest = JSON.parse(
  await readFile(resolve(projectRoot, selectedRelease.manifest), "utf8")
);
const isRulesCandidate = manifest.artifactKind === "physical-rules-candidate";
const rulesVersion = isRulesCandidate ? manifest.rulesVersion : manifest.gameVersion;
const rulesFingerprint = isRulesCandidate
  ? manifest.rulesFingerprint
  : manifest.rulesetFingerprint;
const sessionId = [
  date,
  `${playerCount}p`,
  slug(boardSeed) || "seed",
  rulesFingerprint.replace(/^sha256:/, "").slice(0, 8)
].join("-");
const playtestRoot = input["output-root"]
  ? resolve(input["output-root"])
  : resolve(projectRoot, "evidence/playtests");
const directory = resolve(playtestRoot, sessionId);
if (!directory.startsWith(`${playtestRoot}/`)) {
  throw new Error("Resolved playtest directory escapes its output root.");
}
await mkdir(directory, { recursive: false });

const receipt = {
  schemaVersion: manifest.contracts.playtestReceiptSchemaVersion,
  evidenceType,
  sessionId,
  playedAt,
  game: {
    version: rulesVersion,
    executableVersion: current.gameVersion,
    sourceCommit,
    rulesetFingerprint: rulesFingerprint,
    playtestKitFingerprint: physicalKitManifest.kitFingerprint,
    variantFingerprint: isRulesCandidate
      ? rulesFingerprint
      : manifest.canonicalVariant.fingerprint
  },
  physicalKit: {
    kitId: physicalKitManifest.kitId,
    componentRevision: rulesVersion,
    executableRevision: current.gameVersion,
    sourceCommit,
    label: `Rules ${rulesVersion} · Executable ${current.gameVersion} · Source ${sourceCommit.slice(0, 8)}`,
    mixedRevisions: false,
    exceptions: []
  },
  configuration: {
    playerCount,
    boardSeed,
    factions: Array.from(
      { length: playerCount },
      (_, seat) => `seat_${seat + 1}_unassigned`
    )
  },
  rulesDeviations: [],
  facilitatorInterventions: [],
  notesFile: "notes.md",
  scoresFile: "scores.json"
};
const scores = {
  schemaVersion: 1,
  sessionId,
  finalStandings: [],
  scoringBySource: []
};
const notes = `# ${sessionId}

Rules ${rulesVersion}

Executable reference ${current.gameVersion}

Source commit ${sourceCommit}

## Players and factions

Replace the unassigned faction placeholders in \`receipt.json\`.

## Timing

- Setup:
- Era I:
- Era II:
- Era III:
- Era IV:
- Final scoring:

## Rules questions and interventions

Record every answer or correction in \`receipt.json\` as well.

## Decisions, surprises, and friction

- 

## Postgame explanation

Could every player explain why the winner won?
`;

await Promise.all([
  writeFile(resolve(directory, "receipt.json"), `${JSON.stringify(receipt, null, 2)}\n`, {
    flag: "wx"
  }),
  writeFile(resolve(directory, "scores.json"), `${JSON.stringify(scores, null, 2)}\n`, {
    flag: "wx"
  }),
  writeFile(resolve(directory, "notes.md"), notes, { flag: "wx" })
]);

process.stdout.write(`${directory}\n`);
