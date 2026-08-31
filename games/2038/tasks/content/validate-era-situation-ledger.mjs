import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = resolve(import.meta.dirname, "../..");
const ledgerPath = "content/data/era-situation-ledger.json";
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
  const [headlines, mandates, references, escalations, factions, world] = await Promise.all([
    readJson("content/data/headlines.json"),
    readJson("content/data/mandates.json"),
    readJson("content/data/reference-cards.json"),
    readJson("content/data/escalations.json"),
    readJson("content/data/factions.json"),
    readJson("content/data/world-copy.json")
  ]);
  const registry = new Map();
  for (const headline of headlines.headlines) {
    addSurface(
      registry,
      `headline:${headline.id}`,
      headline.round,
      `content/copy/headlines.json#headlines/${headline.id}`
    );
  }
  for (const mandate of mandates.mandates) {
    addSurface(
      registry,
      `mandate:${mandate.id}`,
      mandate.era,
      `content/copy/mandates.json#mandates/${mandate.id}`
    );
  }
  for (const reference of references.eraCards) {
    addSurface(
      registry,
      `reference:${reference.id}`,
      reference.round,
      `content/copy/reference-cards.json#eraCards/${reference.id}`
    );
  }
  for (const escalation of escalations.escalations) {
    addSurface(
      registry,
      `escalation:${escalation.id}`,
      escalation.unlockedRound,
      `content/copy/escalations.json#escalations/${escalation.id}`
    );
  }
  for (const faction of factions.factions) {
    for (const ability of faction.abilities) {
      addSurface(
        registry,
        `faction:${faction.id}:${ability.id}`,
        ability.round,
        `content/copy/factions.json#factions/${faction.id}/abilities/${ability.id}`
      );
    }
  }
  for (const ending of world.endings) {
    addSurface(
      registry,
      `ending:${ending.id}`,
      4,
      `content/copy/world-copy.json#endings/${ending.id}`
    );
  }
  return registry;
}

function validateDeploymentProfiles(ledger) {
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
    "dist/runtime/secret-objectives.json",
    "dist/runtime/simulation-copy.json"
  ]) {
    if (publicProfile.runtimeArtifacts.includes(forbiddenRuntime) || publicProfile.runtimeArtifacts.includes("*")) {
      throw new Error(`public-playtest must exclude ${forbiddenRuntime}.`);
    }
  }
}

async function assertDeferredTermsAbsentFromBaseline(scenarios) {
  const baselinePaths = [
    "content/copy/core-rules.md",
    "content/copy/map-reference.md",
    "content/copy/component-reference.md",
    "content/copy/card-reference.md",
    "content/copy/world-and-institutions.md",
    "content/copy/game-config.json",
    "content/copy/headlines.json",
    "content/copy/mandates.json",
    "content/copy/reference-cards.json",
    "content/copy/escalations.json",
    "content/copy/factions.json",
    "content/copy/world-copy.json",
    "web/templates/prototype.html",
    "web/templates/first-game-guide.html"
  ];
  const baseline = (await Promise.all(
    baselinePaths.map((path) => readFile(resolve(projectRoot, path), "utf8"))
  )).join("\n").toLocaleLowerCase("en-US");
  for (const scenario of scenarios.filter((entry) => deferredDispositions.has(entry.disposition))) {
    if (baseline.includes(scenario.title.toLocaleLowerCase("en-US"))) {
      throw new Error(`Deferred scenario appears in baseline output: ${scenario.id}`);
    }
  }
}

export async function loadEraSituationLedger() {
  return readJson(ledgerPath);
}

export async function validateEraSituationLedger(ledger) {
  if (ledger?.$schema !== "mandate2038.era-situation-ledger/v1" || ledger.schemaVersion !== 1) {
    throw new Error("Era ledger must use mandate2038.era-situation-ledger/v1.");
  }
  if (ledger.editorialAuthority !== "docs/thematic-content-bible.md") {
    throw new Error("Era ledger must point to the sole thematic editorial authority.");
  }
  validateDeploymentProfiles(ledger);
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
      throw new Error(`Adopted scenario does not preserve its mechanic: ${scenario.id}`);
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
