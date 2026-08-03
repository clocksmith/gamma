import { readFile, mkdir, writeFile } from "node:fs/promises";
import { extname, resolve } from "node:path";
import {
  canonicalJson,
  fingerprintObject,
  loadGameIdentity,
  projectRoot,
  sha256
} from "../lab/versioning/game-identity.js";
import { canonicalRulesVariant } from "../lab/environment/rules-variant.js";
import { contentSourceFiles as declaredContentSourceFiles } from "./content/source-files.mjs";

const arguments_ = process.argv.slice(2);
if (arguments_.includes("--help")) {
  process.stdout.write(
    "Usage: node tasks/create-game-release.mjs [--verify]\n" +
    "Without --verify, writes the version declared by versions/current-release.json.\n"
  );
  process.exit(0);
}
const unknownArguments = arguments_.filter((argument) => argument !== "--verify");
if (unknownArguments.length) {
  throw new TypeError(`Unknown release argument: ${unknownArguments[0]}.`);
}
const verify = arguments_.includes("--verify");
const versionDocument = JSON.parse(
  await readFile(resolve(projectRoot, "versions/current-release.json"), "utf8")
);
const config = JSON.parse(
  await readFile(resolve(projectRoot, "dist/runtime/game-config.json"), "utf8")
);
const contentGraphPath = "content/graph.json";
const contentGraphDocument = JSON.parse(
  await readFile(resolve(projectRoot, contentGraphPath), "utf8")
);
const contentSourceFiles = declaredContentSourceFiles(contentGraphDocument);
const identity = await loadGameIdentity({
  root: projectRoot,
  rulesVariant: canonicalRulesVariant(config)
});
const contentIdentity = await fileIdentity(contentSourceFiles);
const releaseDirectory = resolve(projectRoot, "versions", versionDocument.gameVersion);
const rulesCandidate = versionDocument.rulesCandidate;
const candidateDirectory = rulesCandidate
  ? resolve(projectRoot, "versions", rulesCandidate.version)
  : null;

async function bundledFiles(paths) {
  const files = {};
  for (const path of paths) {
    const contents = await readFile(resolve(projectRoot, path), "utf8");
    files[path] = extname(path) === ".json" ? JSON.parse(contents) : contents;
  }
  return files;
}

async function fileIdentity(paths) {
  const files = {};
  for (const path of [...paths].sort()) {
    const contents = await readFile(resolve(projectRoot, path));
    files[path] = {
      bytes: contents.byteLength,
      sha256: sha256(contents)
    };
  }
  return {
    files,
    fingerprint: fingerprintObject(
      Object.entries(files).map(([path, metadata]) => ({ path, ...metadata }))
    )
  };
}

const manifest = {
  schemaVersion: versionDocument.contracts.releaseManifestSchemaVersion,
  gameVersion: versionDocument.gameVersion,
  releaseStatus: versionDocument.releaseStatus,
  releaseDate: versionDocument.releaseDate,
  rulesetFingerprint: identity.game.rulesetFingerprint,
  mechanicsFingerprint: identity.game.mechanicsFingerprint,
  playtestKitFingerprint: identity.game.playtestKitFingerprint,
  contentGraphFingerprint: contentIdentity.fingerprint,
  contentGraphFiles: contentIdentity.files,
  canonicalVariant: identity.variant,
  engine: {
    id: identity.engine.id,
    version: identity.engine.version,
    coverageId: identity.engine.coverageId,
    fingerprint: identity.engine.fingerprint
  },
  contracts: identity.contracts,
  rng: identity.rng,
  files: identity.game.files,
  kitFiles: identity.game.kitFiles,
  sourcePolicy: "The frontier-rules-v<gameVersion> Git tag identifies the release commit."
};

const bundle = {
  schemaVersion: 1,
  gameVersion: versionDocument.gameVersion,
  rulesetFingerprint: identity.game.rulesetFingerprint,
  mechanicsFingerprint: identity.game.mechanicsFingerprint,
  playtestKitFingerprint: identity.game.playtestKitFingerprint,
  contentGraphFingerprint: contentIdentity.fingerprint,
  canonicalVariantFingerprint: identity.variant.fingerprint,
  contentGraph: await bundledFiles(contentSourceFiles),
  ruleset: await bundledFiles(versionDocument.rulesetFiles),
  playtestKit: await bundledFiles(versionDocument.playtestKitFiles)
};

const current = {
  schemaVersion: 2,
  gameVersion: versionDocument.gameVersion,
  manifest: `versions/${versionDocument.gameVersion}/manifest.json`,
  bundle: `versions/${versionDocument.gameVersion}/game-bundle.json`,
  rulesetFingerprint: identity.game.rulesetFingerprint,
  mechanicsFingerprint: identity.game.mechanicsFingerprint,
  playtestKitFingerprint: identity.game.playtestKitFingerprint,
  contentGraphFingerprint: contentIdentity.fingerprint,
  canonicalVariantFingerprint: identity.variant.fingerprint
};

const artifacts = [
  [resolve(releaseDirectory, "manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`],
  [resolve(releaseDirectory, "game-bundle.json"), `${JSON.stringify(bundle, null, 2)}\n`]
];

if (rulesCandidate) {
  const candidateIdentity = await fileIdentity(rulesCandidate.files);
  const candidateManifest = {
    schemaVersion: versionDocument.contracts.releaseManifestSchemaVersion,
    artifactKind: "physical-rules-candidate",
    rulesVersion: rulesCandidate.version,
    releaseStatus: rulesCandidate.status,
    releaseDate: rulesCandidate.date,
    rulesFingerprint: candidateIdentity.fingerprint,
    contentGraphFingerprint: contentIdentity.fingerprint,
    files: candidateIdentity.files,
    implementation: {
      status: rulesCandidate.implementationStatus,
      implementedByGameVersion: rulesCandidate.implementedByGameVersion,
      executableGameVersion: versionDocument.gameVersion,
      engineCoverageId: versionDocument.engine.coverageId
    },
    contracts: versionDocument.contracts,
    sourcePolicy: "The candidate is physical rules evidence only until implementedByGameVersion is set."
  };
  const candidateBundle = {
    schemaVersion: 1,
    artifactKind: "physical-rules-candidate",
    rulesVersion: rulesCandidate.version,
    rulesFingerprint: candidateIdentity.fingerprint,
    implementationStatus: rulesCandidate.implementationStatus,
    documents: await bundledFiles(rulesCandidate.files)
  };
  current.rulesCandidate = {
    version: rulesCandidate.version,
    status: rulesCandidate.status,
    manifest: `versions/${rulesCandidate.version}/manifest.json`,
    bundle: `versions/${rulesCandidate.version}/rules-candidate-bundle.json`,
    rulesFingerprint: candidateIdentity.fingerprint,
    implementationStatus: rulesCandidate.implementationStatus,
    implementedByGameVersion: rulesCandidate.implementedByGameVersion
  };
  artifacts.push(
    [resolve(candidateDirectory, "manifest.json"), `${JSON.stringify(candidateManifest, null, 2)}\n`],
    [
      resolve(candidateDirectory, "rules-candidate-bundle.json"),
      `${JSON.stringify(candidateBundle, null, 2)}\n`
    ]
  );
}

artifacts.push([
  resolve(projectRoot, "versions/current.json"),
  `${JSON.stringify(current, null, 2)}\n`
]);

if (verify) {
  for (const [path, expected] of artifacts) {
    let actual;
    try {
      actual = await readFile(path, "utf8");
    } catch {
      throw new Error(`Missing generated release artifact: ${path}`);
    }
    if (canonicalJson(JSON.parse(actual)) !== canonicalJson(JSON.parse(expected))) {
      throw new Error(`Stale generated release artifact: ${path}`);
    }
  }
  process.stdout.write(
    `game-release: verified executable ${versionDocument.gameVersion}` +
    `${rulesCandidate ? ` and rules candidate ${rulesCandidate.version}` : ""} ` +
    `${identity.game.rulesetFingerprint}\n`
  );
} else {
  await mkdir(releaseDirectory, { recursive: true });
  if (candidateDirectory) await mkdir(candidateDirectory, { recursive: true });
  for (const [path, contents] of artifacts) await writeFile(path, contents);
  process.stdout.write(
    `game-release: wrote executable ${versionDocument.gameVersion}` +
    `${rulesCandidate ? ` and rules candidate ${rulesCandidate.version}` : ""} ` +
    `${identity.game.rulesetFingerprint}\n`
  );
}
