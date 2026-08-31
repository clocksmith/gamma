import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";
import {
  createLoreSurfaceCatalog,
  validateEraSituationLedger
} from "../tasks/content/era-situation-ledger.mjs";

const projectRoot = resolve(import.meta.dirname, "..");
const readJson = async (relative) =>
  JSON.parse(await readFile(resolve(projectRoot, relative), "utf8"));

async function contractInputs() {
  const [ledger, graph, firebase] = await Promise.all([
    readJson("content/data/era-situation-ledger.json"),
    readJson("content/graph.json"),
    readJson("firebase.json")
  ]);
  return { root: projectRoot, ledger, graph, firebase };
}

test("the canonical lore ledger is a complete non-overlapping surface partition", async () => {
  const inputs = await contractInputs();
  const result = await validateEraSituationLedger(inputs);
  const catalog = await createLoreSurfaceCatalog(projectRoot);
  const bindingIds = inputs.ledger.scenarios.flatMap((scenario) =>
    scenario.bindings.map((binding) => binding.surfaceId)
  );
  const typeCounts = Object.fromEntries(
    [...catalog.values()].reduce((entries, surface) => {
      entries.set(surface.kind, (entries.get(surface.kind) ?? 0) + 1);
      return entries;
    }, new Map())
  );

  assert.deepEqual(result, {
    eras: 4,
    scenarios: 43,
    surfaces: 62,
    profiles: 2
  });
  assert.equal(bindingIds.length, 62);
  assert.equal(new Set(bindingIds).size, 62);
  assert.deepEqual(typeCounts, {
    headline: 24,
    mandate: 12,
    program: 6,
    faction: 12,
    era: 4,
    ending: 4
  });
  assert.deepEqual(inputs.ledger.surfaceContract.typeCounts, typeCounts);
});

test("the lore validator rejects binding, Era, copy, and mechanics drift", async () => {
  const inputs = await contractInputs();
  const firstBinding = inputs.ledger.scenarios[0].bindings[0];

  const duplicate = structuredClone(inputs);
  duplicate.ledger.scenarios[1].bindings.push(
    structuredClone(duplicate.ledger.scenarios[0].bindings[0])
  );
  await assert.rejects(
    validateEraSituationLedger(duplicate),
    /bound more than once/
  );

  const wrongEra = structuredClone(inputs);
  wrongEra.ledger.scenarios[0].bindings[0].expectedEra =
    firstBinding.expectedEra === 4 ? 3 : firstBinding.expectedEra + 1;
  await assert.rejects(validateEraSituationLedger(wrongEra), /Era mismatch/);

  const missingCopy = structuredClone(inputs);
  missingCopy.ledger.scenarios[0].bindings[0].copyAnchors = [
    "copy that does not exist on the governed surface"
  ];
  await assert.rejects(validateEraSituationLedger(missingCopy), /missing copy anchor/);

  const changedMechanic = structuredClone(inputs);
  changedMechanic.ledger.scenarios[0].bindings[0].mechanicsFingerprint =
    "sha256:" + "0".repeat(64);
  await assert.rejects(
    validateEraSituationLedger(changedMechanic),
    /Mechanic preservation fingerprint changed/
  );

  const wrongDeclaredCounts = structuredClone(inputs);
  wrongDeclaredCounts.ledger.surfaceContract.scenarioCount = 42;
  await assert.rejects(
    validateEraSituationLedger(wrongDeclaredCounts),
    /surfaceContract must declare/
  );
});

test("publication profiles enforce public and internal review boundaries", async () => {
  const inputs = await contractInputs();
  const publicProfile = inputs.ledger.deploymentProfiles["public-playtest"];
  const internalProfile = inputs.ledger.deploymentProfiles["internal-review"];

  assert.equal(publicProfile.deployable, true);
  assert.equal(internalProfile.deployable, false);
  assert.equal(inputs.firebase.hosting.public, publicProfile.outputRoot);
  assert.ok(!publicProfile.documentFiles.includes("thematic-content-bible.html"));
  assert.ok(!publicProfile.siteSurfaces.includes("simulation-lab"));
  assert.ok(internalProfile.documentFiles.includes("thematic-content-bible.html"));
  assert.ok(internalProfile.siteSurfaces.includes("simulation-lab"));

  const exposedDocument = structuredClone(inputs);
  exposedDocument.ledger.deploymentProfiles["public-playtest"].documentFiles.push(
    "thematic-content-bible.html"
  );
  await assert.rejects(
    validateEraSituationLedger(exposedDocument),
    /Public playtest exposes internal document/
  );

  const exposedSurface = structuredClone(inputs);
  exposedSurface.ledger.deploymentProfiles["public-playtest"].siteSurfaces.push(
    "simulation-lab"
  );
  await assert.rejects(
    validateEraSituationLedger(exposedSurface),
    /Public playtest exposes internal surface/
  );
});

test("package rename preserves stable legacy game and report identifiers", async () => {
  const [packageManifest, gameConfig, simulationSource] = await Promise.all([
    readJson("package.json"),
    readJson("content/data/game-config.json"),
    readFile(resolve(projectRoot, "web/simulation-app.js"), "utf8")
  ]);
  assert.equal(packageManifest.name, "mandate-2038");
  assert.equal(gameConfig.gameId, "frontier-2038");
  assert.match(simulationSource, /"frontier-2038"/);
});
