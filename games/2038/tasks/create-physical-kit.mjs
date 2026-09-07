import { verifyRelease } from "./release-artifacts.mjs";
import { execFile } from "node:child_process";
import {
  copyFile,
  mkdir,
  readFile,
  rm,
  writeFile
} from "node:fs/promises";
import { resolve } from "node:path";
import { promisify } from "node:util";
import { createHash } from "node:crypto";

const execFileAsync = promisify(execFile);
const projectRoot = resolve(import.meta.dirname, "..");
const buildRoot = resolve(projectRoot, "dist/physical-kit");

const sourceDataFiles = [
  "dist/runtime/content-manifest.json",
  "dist/runtime/factions.json",
  "dist/runtime/game-config.json",
  "dist/runtime/headlines.json",
  "dist/runtime/mandates.json",
  "dist/runtime/reference-cards.json",
  "dist/runtime/projects.json",
  "dist/runtime/world-copy.json"
];

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

async function readJson(path) {
  return JSON.parse(await readFile(resolve(projectRoot, path), "utf8"));
}

async function git(...args) {
  const { stdout } = await execFileAsync("git", args, { cwd: projectRoot });
  return stdout.trim();
}

function labeledRulebook(markdown, identity) {
  const label = [
    `**Physical-kit identity:** Rules ${identity.rulesVersion}`,
    `Executable reference ${identity.executableVersion}`,
    `Source commit ${identity.sourceCommit}`
  ].join(" · ");
  const firstBreak = markdown.indexOf("\n");
  return `${markdown.slice(0, firstBreak + 1)}\n${label}\n${markdown.slice(firstBreak + 1)}`;
}

function labeledGallery(html, identity) {
  const label = `Rules ${identity.rulesVersion} · Executable ${identity.executableVersion} · Source ${identity.sourceCommit}`;
  const escaped = label
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  return html
    .replace(
      "</style>",
      `.kit-identity{font:600 10px/1.35 ui-monospace,monospace;color:#5f6a72;border-top:1px solid #ccd3d8;padding:8px 12px;overflow-wrap:anywhere}.kit-banner{padding:10px 12px;border:1px solid #77838c;background:#eef2f4;font:600 12px/1.4 ui-monospace,monospace}@media print{.sidebar,.search{display:none!important}.layout{display:block}.kit-identity{display:block}.card{break-inside:avoid}}\n</style>`
    )
    .replace(
      '<div class="page-head">',
      `<div class="page-head"><p class="kit-banner">${escaped}</p>`
    )
    .replaceAll(
      "</article>",
      `<footer class="kit-identity">${escaped}</footer></article>`
    );
}

function protocol(identity, source) {
  const section = source.slice(source.indexOf("## Construction comparison and next blind teach"));
  if (!section.startsWith("## Construction comparison")) throw new Error("Missing canonical blind-teach protocol.");
  return `# Physical-test preparation — human session pending

Rules ${identity.rulesVersion} · Executable ${identity.executableVersion}
Source commit ${identity.sourceCommit}
Source published at origin/main: ${identity.sourcePublished}

${section}
`;
}

await verifyRelease(projectRoot);

const status = await git("status", "--porcelain", "--untracked-files=all", "--", ".");
if (status) {
  throw new Error(
    "Physical-kit freeze requires a clean project worktree. Commit or remove project changes first."
  );
}

const sourceCommit = await git("rev-parse", "HEAD");
const remoteCommit = await git("rev-parse", "origin/main");
const localOnly = process.argv.slice(2).includes("--local");
if (sourceCommit !== remoteCommit && !localOnly) {
  throw new Error(
    `Physical-kit freeze requires HEAD to equal origin/main (${sourceCommit} != ${remoteCommit}).`
  );
}

const remoteUrl = await git("remote", "get-url", "origin");
const current = await readJson("versions/current.json");
const executableManifest = await readJson(current.manifest);
const candidate = current.rulesCandidate;
if (!candidate) throw new Error("Current release has no physical-rules candidate.");
const candidateManifest = await readJson(candidate.manifest);
if (
  candidateManifest.implementation?.executableGameVersion !== current.gameVersion ||
  candidate.implementedByGameVersion !== current.gameVersion
) {
  throw new Error("Physical candidate and executable release are not synchronized.");
}

const identity = {
  rulesVersion: candidate.version,
  executableVersion: current.gameVersion,
  sourceCommit,
  sourceRemote: remoteUrl,
  sourcePublished: sourceCommit === remoteCommit,
  rulesFingerprint: candidate.rulesFingerprint,
  rulesetFingerprint: current.rulesetFingerprint,
  mechanicsFingerprint: current.mechanicsFingerprint,
  playtestKitFingerprint: current.playtestKitFingerprint,
  contentGraphFingerprint: current.contentGraphFingerprint,
  engineFingerprint: executableManifest.engine.fingerprint
};
const kitId = `${identity.rulesVersion}-${sourceCommit.slice(0, 8)}`;
const outputRoot = resolve(buildRoot, kitId);
if (!outputRoot.startsWith(`${buildRoot}/`)) {
  throw new Error("Resolved physical-kit output escapes dist/physical-kit.");
}

await rm(outputRoot, { recursive: true, force: true });
await mkdir(resolve(outputRoot, "observer/source-data"), { recursive: true });
await mkdir(resolve(outputRoot, "observer/release"), { recursive: true });
await mkdir(resolve(outputRoot, "observer/contracts"), { recursive: true });

const graph = await readJson("content/graph.json");
for (const file of graph.physicalKit.files) {
  const source = await readFile(resolve(projectRoot, file.source), "utf8");
  const transform = {markdown:labeledRulebook, gallery:labeledGallery,
    protocol:(text, identity) => protocol(identity, text)}[file.transform];
  if (!transform) throw new Error(`Unknown physical-kit transform: ${file.transform}`);
  await mkdir(resolve(outputRoot, file.target, ".."), {recursive:true});
  await writeFile(resolve(outputRoot, file.target), transform(source, identity));
}
await writeFile(
  resolve(outputRoot, "KIT-LABEL.txt"),
  `Rules ${identity.rulesVersion}\nExecutable reference ${identity.executableVersion}\nSource commit ${identity.sourceCommit}\n`
);

for (const path of sourceDataFiles) {
  await copyFile(
    resolve(projectRoot, path),
    resolve(outputRoot, "observer/source-data", path.slice("dist/runtime/".length))
  );
}
await copyFile(
  resolve(projectRoot, current.manifest),
  resolve(outputRoot, "observer/release", "executable-manifest.json")
);
await copyFile(
  resolve(projectRoot, candidate.manifest),
  resolve(outputRoot, "observer/release", "rules-candidate-manifest.json")
);
await copyFile(
  resolve(projectRoot, "lab/contracts/playtest-receipt.schema.json"),
  resolve(outputRoot, "observer/contracts", "playtest-receipt.schema.json")
);

const readme = `# Mandate 2038 controlled physical kit

Rules ${identity.rulesVersion}

Executable reference ${identity.executableVersion}

Source commit ${identity.sourceCommit}

This is a derived controlled-test kit, not a manufacturing package. It contains
one complete rulebook, baseline component masters, the Governance Board ledger,
exact source data, release manifests, receipt contract, and blind-test preparation
protocol under \`observer/\`. Authoring documents and supplementary review books are excluded. Deferred Tactics, secret objectives, and Reserve
Specialists are excluded from the component masters.

Do not mix component revisions. Generate the actual session receipt with
\`npm run playtest:new\` from the same source commit.
`;
await writeFile(resolve(outputRoot, "README.md"), readme);

const relativeFiles = [
  ...graph.physicalKit.files.map(file => file.target),
  "KIT-LABEL.txt",
  "README.md",
  "observer/contracts/playtest-receipt.schema.json",
  "observer/release/executable-manifest.json",
  "observer/release/rules-candidate-manifest.json",
  ...sourceDataFiles.map((path) => `observer/source-data/${path.slice("dist/runtime/".length)}`)
].sort();
const files = {};
for (const path of relativeFiles) {
  const contents = await readFile(resolve(outputRoot, path));
  files[path] = {
    bytes: contents.byteLength,
    sha256: sha256(contents)
  };
}
const kitFingerprint = sha256(
  JSON.stringify(Object.entries(files).map(([path, metadata]) => ({
    path,
    ...metadata
  })))
);
const manifest = {
  schemaVersion: 1,
  artifactKind: "controlled-physical-playtest-kit",
  kitId,
  identity,
  kitFingerprint: `sha256:${kitFingerprint}`,
  playerDocuments: graph.physicalKit.files.filter(file => file.audience === "player" && file.source === "dist/docs/core-rules.md").map(file => file.target),
  baselineModules: [
    "Core Actions",
    "Eras",
    "Headlines",
    "Era Mandates",
    "Build projects",
    "Local Power contracts",
    "Reference Cards",
    "Faction boards",
    "Training deck contract",
    "Map and token contracts"
  ],
  excludedModules: [
    "Tactics",
    "secret objectives",
    "Reserve Specialists"
  ],
  sessions: [],
  sessionStatus: "not-scheduled",

  files
};
await writeFile(
  resolve(outputRoot, "physical-kit-manifest.json"),
  `${JSON.stringify(manifest, null, 2)}\n`
);
await writeFile(
  resolve(buildRoot, "current.json"),
  `${JSON.stringify({
    schemaVersion: 1,
    artifactKind: manifest.artifactKind,
    kitId,
    manifest: `${kitId}/physical-kit-manifest.json`,
    kitFingerprint: manifest.kitFingerprint,
    identity
  }, null, 2)}\n`
);

process.stdout.write(
  `${outputRoot}\nphysical-kit fingerprint: sha256:${kitFingerprint}\n`
);
