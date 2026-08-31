import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { mergeContent } from "./merge.mjs";

export const ledgerPath = "content/data/era-situation-ledger.json";
export const generatedLedgerMarker = "<!-- GENERATED:ERA_SITUATION_LEDGER -->";

const allowedStatuses = new Set(["adopted", "adopted_framing"]);
const expectedSurfaceCounts = Object.freeze({
  headline: 24,
  mandate: 12,
  program: 6,
  faction: 12,
  era: 4,
  ending: 4
});
const profileIds = Object.freeze(["public-playtest", "internal-review"]);
const forbiddenPublicDocuments = new Set([
  "balance-and-exploitability.html",
  "comparisons.html",
  "complexity-reduction-protocol.html",
  "defect-investigation-and-closure.html",
  "design-decisions.html",
  "manufacturing-and-publishing-study.html",
  "playtesting-and-evidence.html",
  "rule-change-register.html",
  "simulation-and-player-strategies.html",
  "thematic-content-bible.html"
]);

function canonicalValue(value) {
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(
    Object.keys(value)
      .sort()
      .map((key) => [key, canonicalValue(value[key])])
  );
}

function sha256(value) {
  return `sha256:${createHash("sha256")
    .update(JSON.stringify(canonicalValue(value)))
    .digest("hex")}`;
}

function without(value, omitted) {
  return Object.fromEntries(
    Object.entries(value).filter(([key]) => !omitted.has(key))
  );
}

async function readJson(root, relative) {
  return JSON.parse(await readFile(resolve(root, relative), "utf8"));
}

async function composedDocument(root, name) {
  const basePath = `content/data/${name}.json`;
  const overlayPath = `content/copy/${name}.json`;
  const [base, overlay] = await Promise.all([
    readJson(root, basePath),
    readJson(root, overlayPath)
  ]);
  return mergeContent(base, overlay.content, overlayPath);
}

function surface({ id, era, kind, record, omittedFields, copyFields }) {
  const copy = Object.fromEntries(
    copyFields
      .filter((field) => record[field] !== undefined)
      .map((field) => [field, record[field]])
  );
  for (const [field, value] of Object.entries(copy)) {
    if (typeof value !== "string" || !value.trim()) {
      throw new Error(`${id}.${field} must be complete copy.`);
    }
  }
  return {
    id,
    era,
    kind,
    copy,
    mechanicsFingerprint: sha256(without(record, new Set(["id", ...omittedFields])))
  };
}

export async function createLoreSurfaceCatalog(root) {
  const [headlines, mandates, programs, references, factions, world] = await Promise.all([
    composedDocument(root, "headlines"),
    composedDocument(root, "mandates"),
    composedDocument(root, "escalations"),
    composedDocument(root, "reference-cards"),
    composedDocument(root, "factions"),
    composedDocument(root, "world-copy")
  ]);
  const catalog = new Map();
  const add = (entry) => {
    if (catalog.has(entry.id)) throw new Error(`Duplicate lore surface: ${entry.id}`);
    catalog.set(entry.id, entry);
  };

  for (const record of headlines.headlines) {
    add(surface({
      id: `headline:${record.id}`,
      era: record.round,
      kind: "headline",
      record,
      omittedFields: ["name", "strapline", "newswire", "quote"],
      copyFields: ["name", "text", "strapline", "newswire", "quote", "profileText"]
    }));
  }
  for (const record of mandates.mandates) {
    add(surface({
      id: `mandate:${record.id}`,
      era: record.era,
      kind: "mandate",
      record,
      omittedFields: ["name", "flavorText"],
      copyFields: ["name", "rulesText", "flavorText"]
    }));
  }
  for (const record of programs.escalations) {
    add(surface({
      id: `program:${record.id}`,
      era: record.unlockedRound,
      kind: "program",
      record,
      omittedFields: ["name", "displayName", "flavorText"],
      copyFields: ["name", "displayName", "text", "flavorText"]
    }));
  }
  for (const faction of factions.factions) {
    for (const ability of faction.abilities) {
      add(surface({
        id: `faction:${faction.id}:${ability.id}`,
        era: ability.round,
        kind: "faction",
        record: ability,
        omittedFields: ["name", "displayName", "timingLabel", "flavorText"],
        copyFields: ["name", "displayName", "timingLabel", "text", "flavorText"]
      }));
    }
  }
  for (const record of references.eraCards) {
    add(surface({
      id: `era:${record.id}`,
      era: record.round,
      kind: "era",
      record,
      omittedFields: ["name", "strapline", "loreText"],
      copyFields: ["name", "strapline", "loreText", "rulesText", "unlockText"]
    }));
  }
  for (const record of world.endings) {
    add(surface({
      id: `ending:${record.id}`,
      era: 4,
      kind: "ending",
      record,
      omittedFields: ["name", "text"],
      copyFields: ["name", "condition", "text"]
    }));
  }
  return catalog;
}

function requireString(value, label) {
  if (typeof value !== "string" || !value.trim()) {
    throw new Error(`${label} must be a non-empty string.`);
  }
}

function requireUniqueStrings(values, label) {
  if (!Array.isArray(values) || values.length === 0) {
    throw new Error(`${label} must be a non-empty array.`);
  }
  for (const value of values) requireString(value, label);
  if (new Set(values).size !== values.length) {
    throw new Error(`${label} contains duplicates.`);
  }
}

async function browserRuntimeDependencies(root, profile) {
  const dependencies = new Set();
  const sourceFiles = [
    ...profile.webFiles.map((relative) => `web/${relative}`),
    ...profile.labModules.map((relative) => `lab/${relative}`)
  ];
  for (const relative of sourceFiles) {
    const source = await readFile(resolve(root, relative), "utf8");
    for (const match of source.matchAll(/dist\/runtime\/([a-z0-9-]+\.json)/g)) {
      dependencies.add(`dist/runtime/${match[1]}`);
    }
    for (const match of source.matchAll(/readJson\(["']([a-z0-9-]+\.json)["']\)/g)) {
      dependencies.add(`dist/runtime/${match[1]}`);
    }
  }
  return [...dependencies].sort();
}

async function validateProfiles(root, ledger, graph, firebase) {
  const profiles = ledger.deploymentProfiles;
  if (!profiles || typeof profiles !== "object" || Array.isArray(profiles)) {
    throw new Error("deploymentProfiles must be an object.");
  }
  if (JSON.stringify(Object.keys(profiles).sort()) !== JSON.stringify([...profileIds].sort())) {
    throw new Error(`deploymentProfiles must contain exactly: ${profileIds.join(", ")}.`);
  }
  const publicProfile = profiles["public-playtest"];
  const internalProfile = profiles["internal-review"];
  if (publicProfile.deployable !== true) {
    throw new Error("public-playtest must be the deployable profile.");
  }
  if (internalProfile.deployable !== false) {
    throw new Error("internal-review must be non-deployable.");
  }
  if (publicProfile.outputRoot === internalProfile.outputRoot) {
    throw new Error("Deployment profiles must use different output roots.");
  }
  for (const [id, profile] of Object.entries(profiles)) {
    requireString(profile.outputRoot, `${id}.outputRoot`);
    if (!profile.outputRoot.startsWith("dist/") || profile.outputRoot.includes("..")) {
      throw new Error(`${id}.outputRoot must be a project-local dist path.`);
    }
    for (const field of [
      "documentFiles",
      "siteSurfaces",
      "runtimeArtifacts",
      "webFiles",
      "labModules"
    ]) {
      requireUniqueStrings(profile[field], `${id}.${field}`);
      if (profile[field].some((value) => value.startsWith("/") || value.includes(".."))) {
        throw new Error(`${id}.${field} must contain project-local relative paths.`);
      }
    }
  }
  if (firebase?.hosting?.public !== publicProfile.outputRoot) {
    throw new Error("firebase.json must point exclusively at the public-playtest output root.");
  }
  for (const document of publicProfile.documentFiles) {
    if (forbiddenPublicDocuments.has(document)) {
      throw new Error(`Public playtest exposes internal document: ${document}`);
    }
  }
  for (const forbidden of ["simulation-lab", "complete-gallery"]) {
    if (publicProfile.siteSurfaces.includes(forbidden)) {
      throw new Error(`Public playtest exposes internal surface: ${forbidden}`);
    }
  }
  for (const required of ["game", "first-game-guide", "baseline-gallery"]) {
    if (!publicProfile.siteSurfaces.includes(required)) {
      throw new Error(`Public playtest is missing required surface: ${required}`);
    }
  }
  const browserRuntime = await browserRuntimeDependencies(root, publicProfile);
  if (JSON.stringify([...publicProfile.runtimeArtifacts].sort()) !==
      JSON.stringify(browserRuntime)) {
    throw new Error(
      "Public playtest runtime artifacts do not match the generated browser dependency closure."
    );
  }
  const graphRuntime = graph.artifacts
    .map((artifact) => artifact.target)
    .filter((target) => /^dist\/runtime\/[^/]+\.json$/.test(target))
    .sort();
  if (JSON.stringify([...internalProfile.runtimeArtifacts].sort()) !== JSON.stringify(graphRuntime)) {
    throw new Error("Internal review must retain every graph-owned runtime artifact.");
  }
  for (const required of ["simulation-lab", "complete-gallery"]) {
    if (!internalProfile.siteSurfaces.includes(required)) {
      throw new Error(`Internal review is missing required surface: ${required}`);
    }
  }
}

export async function validateEraSituationLedger({ root, ledger, graph, firebase }) {
  if (!ledger) ledger = await readJson(root, ledgerPath);
  if (!graph) graph = await readJson(root, "content/graph.json");
  if (!firebase) firebase = await readJson(root, "firebase.json");
  if (ledger.schemaVersion !== 1) throw new Error("Lore ledger schemaVersion must be 1.");
  if (ledger.authority !== "canonical-era-situation-contract") {
    throw new Error("Lore ledger authority declaration is invalid.");
  }
  if (!Array.isArray(ledger.eras) || ledger.eras.length !== 4) {
    throw new Error("Lore ledger must declare exactly four Eras.");
  }
  const eraNumbers = ledger.eras.map((era) => era.number);
  if (JSON.stringify(eraNumbers) !== JSON.stringify([1, 2, 3, 4])) {
    throw new Error("Lore ledger Eras must be ordered 1 through 4.");
  }
  for (const era of ledger.eras) {
    requireString(era.id, `Era ${era.number}.id`);
    requireString(era.name, `Era ${era.number}.name`);
    requireString(era.changeInStatus, `Era ${era.number}.changeInStatus`);
    requireString(era.centralConflict, `Era ${era.number}.centralConflict`);
  }
  if (!Array.isArray(ledger.scenarios) || ledger.scenarios.length !== 43) {
    throw new Error("Lore ledger must declare exactly 43 scenarios.");
  }
  const catalog = await createLoreSurfaceCatalog(root);
  if (catalog.size !== 62) {
    throw new Error(`Lore surface catalog must contain 62 surfaces, found ${catalog.size}.`);
  }
  const scenarioIds = new Set();
  const boundSurfaces = new Set();
  for (const scenario of ledger.scenarios) {
    requireString(scenario.id, "scenario.id");
    requireString(scenario.title, `${scenario.id}.title`);
    requireString(scenario.editorialIntent, `${scenario.id}.editorialIntent`);
    if (scenarioIds.has(scenario.id)) throw new Error(`Duplicate scenario: ${scenario.id}`);
    scenarioIds.add(scenario.id);
    if (!allowedStatuses.has(scenario.status)) {
      throw new Error(`Invalid adoption status for ${scenario.id}: ${scenario.status}`);
    }
    if (!Number.isInteger(scenario.primaryEra) || scenario.primaryEra < 1 || scenario.primaryEra > 4) {
      throw new Error(`Invalid primary Era for ${scenario.id}.`);
    }
    if (!Array.isArray(scenario.bindings) || scenario.bindings.length === 0) {
      throw new Error(`${scenario.id} must bind at least one game surface.`);
    }
    for (const binding of scenario.bindings) {
      requireString(binding.surfaceId, `${scenario.id}.surfaceId`);
      const found = catalog.get(binding.surfaceId);
      if (!found) throw new Error(`${scenario.id} binds unknown surface: ${binding.surfaceId}`);
      if (boundSurfaces.has(binding.surfaceId)) {
        throw new Error(`Lore surface is bound more than once: ${binding.surfaceId}`);
      }
      boundSurfaces.add(binding.surfaceId);
      if (binding.expectedEra !== found.era) {
        throw new Error(
          `${binding.surfaceId} Era mismatch: ledger ${binding.expectedEra}, source ${found.era}.`
        );
      }
      requireUniqueStrings(binding.copyAnchors, `${binding.surfaceId}.copyAnchors`);
      const copyText = Object.values(found.copy)
        .filter((value) => typeof value === "string")
        .join("\n")
        .toLocaleLowerCase("en-US");
      for (const anchor of binding.copyAnchors) {
        if (!copyText.includes(anchor.toLocaleLowerCase("en-US"))) {
          throw new Error(`${binding.surfaceId} is missing copy anchor: ${anchor}`);
        }
      }
      for (const [field, value] of Object.entries(found.copy)) {
        if (value !== undefined && (typeof value !== "string" || !value.trim())) {
          throw new Error(`${binding.surfaceId}.${field} must be complete copy.`);
        }
      }
      if (binding.mechanicsFingerprint !== found.mechanicsFingerprint) {
        throw new Error(`Mechanic preservation fingerprint changed for ${binding.surfaceId}.`);
      }
    }
  }
  if (boundSurfaces.size !== 62) {
    throw new Error(`Lore ledger must bind 62 unique surfaces, found ${boundSurfaces.size}.`);
  }
  const missing = [...catalog.keys()].filter((id) => !boundSurfaces.has(id));
  if (missing.length) throw new Error(`Unbound lore surfaces: ${missing.join(", ")}`);
  const counts = Object.fromEntries(Object.keys(expectedSurfaceCounts).map((kind) => [kind, 0]));
  for (const entry of catalog.values()) counts[entry.kind] += 1;
  if (JSON.stringify(counts) !== JSON.stringify(expectedSurfaceCounts)) {
    throw new Error(`Lore surface type counts changed: ${JSON.stringify(counts)}.`);
  }
  const declaredContract = ledger.surfaceContract;
  if (declaredContract?.scenarioCount !== 43 ||
      declaredContract?.uniqueSurfaceCount !== 62 ||
      JSON.stringify(declaredContract?.typeCounts) !== JSON.stringify(expectedSurfaceCounts)) {
    throw new Error("surfaceContract must declare the enforced 43-scenario, 62-surface partition.");
  }
  await validateProfiles(root, ledger, graph, firebase);
  return {
    eras: ledger.eras.length,
    scenarios: ledger.scenarios.length,
    surfaces: boundSurfaces.size,
    profiles: Object.keys(ledger.deploymentProfiles).length
  };
}

function markdownCell(value) {
  return String(value).replaceAll("|", "\\|").replaceAll("\n", " ");
}

export function renderEraSituationLedgerMarkdown(ledger) {
  const lines = [
    "## Canonical Era and situation ledger",
    "",
    "This section is generated from `content/data/era-situation-ledger.json`.",
    "The JSON contract owns adoption status, primary Era, game-surface binding,",
    "copy anchors, mechanic-preservation fingerprints, and publication profiles.",
    "Do not edit this projection by hand.",
    "",
    "### Four-Era contract",
    "",
    "| Era | Change in status | Central conflict |",
    "| --- | --- | --- |",
    ...ledger.eras.map((era) =>
      `| ${era.number}. ${markdownCell(era.name)} | ${markdownCell(era.changeInStatus)} | ${markdownCell(era.centralConflict)} |`
    ),
    "",
    "### Admitted situations and uniquely owned surfaces",
    "",
    `The contract admits **${ledger.scenarios.length} situations** and partitions ` +
      `**${ledger.scenarios.flatMap((scenario) => scenario.bindings).length} game surfaces**.`,
    "Every surface appears exactly once.",
    "",
    "| Situation | Status | Primary Era | Editorial intent | Bound surfaces |",
    "| --- | --- | ---: | --- | --- |",
    ...ledger.scenarios.map((scenario) =>
      `| ${markdownCell(scenario.title)} | ${markdownCell(scenario.status)} | ` +
      `${scenario.primaryEra} | ${markdownCell(scenario.editorialIntent)} | ` +
      `${scenario.bindings.map((binding) => `\`${binding.surfaceId}\``).join(", ")} |`
    ),
    ""
  ];
  return lines.join("\n");
}
