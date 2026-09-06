import { readFile } from "node:fs/promises";
import { dirname, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { buildScenarioIndex, scenarioSurfaces } from "./scenario-index.mjs";
import { documentSection, playerContent } from "./authored.mjs";

const projectRoot = resolve(import.meta.dirname, "../..");
const adoptedDispositions = new Set(["adopted", "adopted-framing"]);
const deferredDispositions = new Set(["deferred", "research-backlog"]);
const expectedEraIds = ["progress", "capacity", "authority", "continuity"];

async function readJson(path) {
  return JSON.parse(await readFile(resolve(projectRoot, path), "utf8"));
}

function requireString(value, label) {
  if (typeof value !== "string" || !value.trim()) {
    throw new Error(`${label} must be a non-empty string.`);
  }
}

function requireStringArray(value, label) {
  if (!Array.isArray(value) || !value.every((entry) => typeof entry === "string" && entry.trim())) {
    throw new Error(`${label} must be an array of non-empty strings.`);
  }
}

function addSurface(registry, surfaceId, eraOrder, copyReference) {
  if (registry.has(surfaceId)) throw new Error(`Duplicate canonical surface: ${surfaceId}`);
  registry.set(surfaceId, { eraOrder, copyReference });
}

async function canonicalSurfaceRegistry() {
  const registry = new Map();
  for (const surface of await scenarioSurfaces()) {
    addSurface(registry, surface.surfaceId, surface.eraOrder, surface.copyReference);
  }
  return registry;
}

function assertPublicationPath(path, label) {
  requireString(path, label);
  if (path.startsWith("/") || path.split("/").includes("..")) {
    throw new Error(`${label} must be a project-relative path.`);
  }
}

function importedModuleSpecifiers(source) {
  return [...source.matchAll(
    /\b(?:import|export)\s+(?:[\s\S]*?\s+from\s+)?["']([^"']+)["']/g
  )].map((match) => match[1]);
}

function runtimeReferences(source) {
  const names = new Set();
  for (const match of source.matchAll(/dist\/runtime\/([a-z0-9-]+\.json)/g)) {
    names.add(`dist/runtime/${match[1]}`);
  }
  for (const match of source.matchAll(/\breadJson\(["']([a-z0-9-]+\.json)["']\)/g)) {
    names.add(`dist/runtime/${match[1]}`);
  }
  return names;
}

async function validatePublicationDependencies(ledger) {
  const graph = await readJson("content/graph.json");
  const declaredRuntime = new Set(
    graph.artifacts
      .map((artifact) => artifact.target)
      .filter((target) => /^dist\/runtime\/[^/]+\.json$/.test(target))
  );
  const webRoot = resolve(projectRoot, "web");
  const labRoot = resolve(projectRoot, "lab");
  for (const [profileId, profile] of Object.entries(ledger.deploymentProfiles)) {
    const publishedWeb = new Set(profile.webFiles);
    const publishedLab = new Set(profile.labModules);
    const referencedRuntime = new Set();
    for (const [root, paths, label] of [
      [webRoot, profile.webFiles, "web file"],
      [labRoot, profile.labModules, "lab module"]
    ]) {
      for (const path of paths) {
        assertPublicationPath(path, `Deployment profile ${profileId} ${label}`);
        const absolute = resolve(root, path);
        let source;
        try {
          source = await readFile(absolute, "utf8");
        } catch (error) {
          if (error.code === "ENOENT") {
            throw new Error(`Deployment profile ${profileId} references missing ${label}: ${path}`);
          }
          throw error;
        }
        if (!path.endsWith(".js")) continue;
        for (const target of runtimeReferences(source)) referencedRuntime.add(target);
        for (const specifier of importedModuleSpecifiers(source)) {
          let imported;
          if (specifier.startsWith("/web/")) imported = resolve(webRoot, specifier.slice(5));
          else if (specifier.startsWith("/lab/")) imported = resolve(labRoot, specifier.slice(5));
          else if (specifier.startsWith(".")) imported = resolve(dirname(absolute), specifier);
          else continue;
          const webRelative = relative(webRoot, imported);
          const labRelative = relative(labRoot, imported);
          if (!webRelative.startsWith("..") && !publishedWeb.has(webRelative)) {
            throw new Error(
              `Deployment profile ${profileId} omits imported web module ${webRelative} required by ${path}.`
            );
          }
          if (!labRelative.startsWith("..") && !publishedLab.has(labRelative)) {
            throw new Error(
              `Deployment profile ${profileId} omits imported lab module ${labRelative} required by ${path}.`
            );
          }
        }
      }
    }
    const runtimeArtifacts = profile.runtimeArtifacts.includes("*")
      ? declaredRuntime
      : new Set(profile.runtimeArtifacts);
    for (const target of runtimeArtifacts) {
      if (!declaredRuntime.has(target)) {
        throw new Error(`Deployment profile ${profileId} references undeclared runtime artifact: ${target}`);
      }
    }
    const missing = [...referencedRuntime].filter((target) => !runtimeArtifacts.has(target));
    if (missing.length) {
      throw new Error(
        `Deployment profile ${profileId} omits runtime dependencies: ${missing.sort().join(", ")}`
      );
    }
    if (profileId === "public-playtest") {
      const unused = [...runtimeArtifacts].filter((target) => !referencedRuntime.has(target));
      if (unused.length) {
        throw new Error(
          `Deployment profile ${profileId} publishes unreferenced runtime artifacts: ${unused.sort().join(", ")}`
        );
      }
    }
  }
}

async function validateDeploymentProfiles(ledger) {
  const profiles = ledger.deploymentProfiles;
  if (!profiles || typeof profiles !== "object" || Array.isArray(profiles)) {
    throw new Error("Era ledger must declare deploymentProfiles.");
  }
  const profileIds = Object.keys(profiles).sort();
  if (profileIds.join(",") !== "internal-review,public-playtest") {
    throw new Error("Era ledger must declare only internal-review and public-playtest profiles.");
  }
  for (const [id, profile] of Object.entries(profiles)) {
    if (typeof profile.deployable !== "boolean" || typeof profile.accessControlled !== "boolean") {
      throw new Error(`Deployment profile ${id} must declare deployable and accessControlled.`);
    }
    requireString(profile.outputRoot, `Deployment profile ${id} outputRoot`);
    requireString(profile.feedbackUrl, `Deployment profile ${id} feedbackUrl`);
    requireStringArray(profile.interfaces, `Deployment profile ${id} interfaces`);
    requireStringArray(profile.documents, `Deployment profile ${id} documents`);
    requireStringArray(profile.galleries, `Deployment profile ${id} galleries`);
    requireStringArray(profile.runtimeArtifacts, `Deployment profile ${id} runtimeArtifacts`);
    requireStringArray(profile.webFiles, `Deployment profile ${id} webFiles`);
    requireStringArray(profile.labModules, `Deployment profile ${id} labModules`);
  }
  const publicProfile = profiles["public-playtest"];
  const reviewProfile = profiles["internal-review"];
  if (!publicProfile.deployable || publicProfile.accessControlled) {
    throw new Error("public-playtest must be deployable public static content.");
  }
  if (reviewProfile.deployable || reviewProfile.accessControlled) {
    throw new Error("internal-review must remain non-deployable until real access control exists.");
  }
  requireString(reviewProfile.warning, "internal-review warning");
  for (const forbiddenDocument of [
    "thematic-content-bible.html",
    "manufacturing-and-publishing-study.html",
    "balance-and-exploitability.html",
    "design-decisions.html",
    "defect-investigation-and-closure.html",
    "simulation-and-player-strategies.html",
    "optional-tactics.html"
  ]) {
    if (publicProfile.documents.includes(forbiddenDocument) || publicProfile.documents.includes("*")) {
      throw new Error(`public-playtest must exclude ${forbiddenDocument}.`);
    }
  }
  if (publicProfile.interfaces.includes("simulation-lab")) {
    throw new Error("public-playtest must exclude the Simulation Lab.");
  }
  if (publicProfile.galleries.includes("complete")) {
    throw new Error("public-playtest must exclude the complete gallery.");
  }
  for (const forbiddenRuntime of [
    "dist/runtime/tactics.json",
    "dist/runtime/reserve-specialists.json",
    "dist/runtime/secret-objectives.json"
  ]) {
    if (publicProfile.runtimeArtifacts.includes(forbiddenRuntime) || publicProfile.runtimeArtifacts.includes("*")) {
      throw new Error(`public-playtest must exclude ${forbiddenRuntime}.`);
    }
  }
  await validatePublicationDependencies(ledger);
}

async function assertDeferredTermsAbsentFromBaseline(scenarios) {
  const baselinePaths = [
    "rules.md",
    "content/templates/map-reference.md",
    "content/templates/component-reference.md",
    "content/templates/card-reference.md",
    "world.md",
    "components/game.json",
    "components/headlines.json",
    "components/mandates.json",
    "components/reference-cards.json",
    "components/programs.json",
    "components/factions.json",
    "components/world.json",
    "web/templates/prototype.html",
    "web/templates/first-game-guide.html"
  ];
  const baseline = (await Promise.all(
    baselinePaths.map(async path => {
      const source = await readFile(resolve(projectRoot, path), "utf8");
      if (path === "world.md") return documentSection(source, "player-world");
      return path.endsWith(".json") ? JSON.stringify(playerContent(JSON.parse(source))) : source;
    })
  )).join("\n").toLocaleLowerCase("en-US");
  for (const scenario of scenarios.filter((entry) => deferredDispositions.has(entry.disposition))) {
    if (baseline.includes(scenario.title.toLocaleLowerCase("en-US"))) {
      throw new Error(`Deferred scenario appears in baseline output: ${scenario.id}`);
    }
  }
}

export async function loadEraSituationLedger() {
  return buildScenarioIndex();
}

export async function validateEraSituationLedger(ledger) {
  if (ledger?.$schema !== "mandate2038.era-situation-ledger/v1" || ledger.schemaVersion !== 1) {
    throw new Error("Era ledger must use mandate2038.era-situation-ledger/v1.");
  }
  if (ledger.editorialAuthority !== "world.md") {
    throw new Error("Era ledger must point to the sole thematic editorial authority.");
  }
  await validateDeploymentProfiles(ledger);
  if (!Array.isArray(ledger.eras) || ledger.eras.length !== expectedEraIds.length) {
    throw new Error("Era ledger must declare exactly four ordered Eras.");
  }
  const erasById = new Map();
  const threadIdsByEra = new Map();
  for (const [index, era] of ledger.eras.entries()) {
    if (era.id !== expectedEraIds[index] || era.order !== index + 1) {
      throw new Error(`Era ${index + 1} must be ${expectedEraIds[index]}.`);
    }
    requireString(era.statusChange, `Era ${era.id} statusChange`);
    requireString(era.centralConflict, `Era ${era.id} centralConflict`);
    if (!Array.isArray(era.causalThreads) || era.causalThreads.length === 0) {
      throw new Error(`Era ${era.id} must declare causalThreads.`);
    }
    const threadIds = new Set();
    for (const thread of era.causalThreads) {
      requireString(thread.id, `Era ${era.id} causal thread ID`);
      requireString(thread.summary, `Era ${era.id} causal thread ${thread.id}`);
      if (threadIds.has(thread.id)) throw new Error(`Duplicate causal thread in ${era.id}: ${thread.id}`);
      threadIds.add(thread.id);
    }
    erasById.set(era.id, era);
    threadIdsByEra.set(era.id, threadIds);
  }
  if (!Array.isArray(ledger.scenarios) || ledger.scenarios.length === 0) {
    throw new Error("Era ledger must declare scenarios.");
  }

  const registry = await canonicalSurfaceRegistry();
  const seenScenarioIds = new Set();
  const seenSurfaceIds = new Set();
  const scenarioCountByEra = new Map(expectedEraIds.map((id) => [id, 0]));
  for (const scenario of ledger.scenarios) {
    requireString(scenario.id, "Scenario ID");
    requireString(scenario.title, `Scenario ${scenario.id} title`);
    if (seenScenarioIds.has(scenario.id)) throw new Error(`Duplicate scenario ID: ${scenario.id}`);
    seenScenarioIds.add(scenario.id);
    if (!erasById.has(scenario.eraId)) throw new Error(`Unknown Era for scenario ${scenario.id}: ${scenario.eraId}`);
    if (!adoptedDispositions.has(scenario.disposition) && !deferredDispositions.has(scenario.disposition)) {
      throw new Error(`Invalid scenario disposition for ${scenario.id}: ${scenario.disposition}`);
    }
    requireStringArray(scenario.concepts, `Scenario ${scenario.id} concepts`);
    requireStringArray(scenario.causalThreadIds, `Scenario ${scenario.id} causalThreadIds`);
    for (const threadId of scenario.causalThreadIds) {
      if (!threadIdsByEra.get(scenario.eraId).has(threadId)) {
        throw new Error(`Scenario ${scenario.id} references an unknown ${scenario.eraId} causal thread: ${threadId}`);
      }
    }
    requireString(scenario.publicBenefit, `Scenario ${scenario.id} publicBenefit`);
    requireString(scenario.institutionalConsequence, `Scenario ${scenario.id} institutionalConsequence`);
    if (!Array.isArray(scenario.surfaceBindings)) {
      throw new Error(`Scenario ${scenario.id} surfaceBindings must be an array.`);
    }
    requireString(scenario.mechanicPreservation?.status, `Scenario ${scenario.id} mechanic preservation status`);
    requireString(scenario.mechanicPreservation?.summary, `Scenario ${scenario.id} mechanic preservation summary`);
    requireStringArray(scenario.deploymentProfiles, `Scenario ${scenario.id} deploymentProfiles`);
    for (const profileId of scenario.deploymentProfiles) {
      if (!ledger.deploymentProfiles[profileId]) {
        throw new Error(`Scenario ${scenario.id} references an unknown deployment profile: ${profileId}`);
      }
    }

    const adopted = adoptedDispositions.has(scenario.disposition);
    if (adopted && scenario.surfaceBindings.length === 0) {
      throw new Error(`Adopted scenario lacks a game-surface binding: ${scenario.id}`);
    }
    if (adopted && scenario.mechanicPreservation.status !== "retained") {
      const revision = scenario.mechanicPreservation.revision;
      if (scenario.mechanicPreservation.status !== "revised" ||
          !((revision?.decisionId === "user-selected-full-simplification" &&
            revision?.record === "docs/design-decisions.md#full-simplification-candidate") ||
           (revision?.decisionId === "user-selected-three-cuts" &&
            revision?.record === "docs/design-decisions.md#three-cuts-candidate"))) {
        throw new Error(`Adopted scenario lacks an authorized mechanic revision: ${scenario.id}`);
      }
    }
    if (adopted && !scenario.deploymentProfiles.includes("public-playtest")) {
      throw new Error(`Adopted scenario is absent from public-playtest: ${scenario.id}`);
    }
    if (!adopted && scenario.surfaceBindings.length !== 0) {
      throw new Error(`Deferred scenario has an unauthorized game-surface binding: ${scenario.id}`);
    }
    if (!adopted && scenario.deploymentProfiles.includes("public-playtest")) {
      throw new Error(`Deferred scenario enters public-playtest: ${scenario.id}`);
    }

    const eraOrder = erasById.get(scenario.eraId).order;
    for (const binding of scenario.surfaceBindings) {
      requireString(binding?.surfaceId, `Scenario ${scenario.id} surface ID`);
      requireString(binding?.copyReference, `Scenario ${scenario.id} copy reference`);
      const canonical = registry.get(binding.surfaceId);
      if (!canonical) throw new Error(`Unknown game-surface binding: ${binding.surfaceId}`);
      if (canonical.eraOrder !== eraOrder) {
        if (binding.eraRelation !== "later-expression" || canonical.eraOrder <= eraOrder) {
          throw new Error(
            `Scenario ${scenario.id} binds ${binding.surfaceId} to Era ${canonical.eraOrder}, not Era ${eraOrder}.`
          );
        }
      } else if (binding.eraRelation !== undefined) {
        throw new Error(`Same-Era binding must not declare eraRelation: ${binding.surfaceId}`);
      }
      if (canonical.copyReference !== binding.copyReference) {
        throw new Error(`Invalid copy reference for ${binding.surfaceId}: ${binding.copyReference}`);
      }
      if (seenSurfaceIds.has(binding.surfaceId)) {
        throw new Error(`Game surface appears in more than one scenario: ${binding.surfaceId}`);
      }
      seenSurfaceIds.add(binding.surfaceId);
    }
    scenarioCountByEra.set(scenario.eraId, scenarioCountByEra.get(scenario.eraId) + 1);
  }
  for (const [eraId, count] of scenarioCountByEra) {
    if (count === 0) throw new Error(`Era has no scenarios: ${eraId}`);
  }
  const missingSurfaces = [...registry.keys()].filter((surfaceId) => !seenSurfaceIds.has(surfaceId));
  if (missingSurfaces.length) {
    throw new Error(`Deployed game surfaces absent from the Era ledger: ${missingSurfaces.join(", ")}`);
  }
  await assertDeferredTermsAbsentFromBaseline(ledger.scenarios);
  return {
    eras: ledger.eras.length,
    scenarios: ledger.scenarios.length,
    surfaces: seenSurfaceIds.size
  };
}

const isCli = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  const result = await validateEraSituationLedger(await loadEraSituationLedger());
  process.stdout.write(
    `era-situation-ledger: verified ${result.eras} Eras, ${result.scenarios} scenarios, and ${result.surfaces} game surfaces\n`
  );
}
