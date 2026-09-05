import assert from "node:assert/strict";
import test from "node:test";
import {
  loadEraSituationLedger,
  validateEraSituationLedger
} from "../tasks/content/validate-era-situation-ledger.mjs";

function clone(value) {
  return structuredClone(value);
}

test("Era situation ledger binds every deployed era surface exactly once", async () => {
  const ledger = await loadEraSituationLedger();
  const result = await validateEraSituationLedger(ledger);
  assert.deepEqual(result, { eras: 4, scenarios: 40, surfaces: 54 });
  assert.deepEqual(ledger.eras.map(({ id, order }) => [id, order]), [
    ["progress", 1],
    ["capacity", 2],
    ["authority", 3],
    ["continuity", 4]
  ]);
});

test("Era situation ledger makes later surface expression explicit", async () => {
  const ledger = await loadEraSituationLedger();
  const scenario = ledger.scenarios.find((entry) => entry.id === "wartime-water-bridge");
  assert.equal(scenario.eraId, "capacity");
  assert.deepEqual(scenario.surfaceBindings, [
    {
      surfaceId: "faction:coalition_lab:strategic_partnership",
      copyReference: "components/factions.json#factions/coalition_lab/abilities/strategic_partnership",
      eraRelation: "later-expression"
    }
  ]);
  await validateEraSituationLedger(ledger);
});

test("Era situation ledger rejects adopted scenarios without a surface binding", async () => {
  const ledger = clone(await loadEraSituationLedger());
  ledger.scenarios.find((scenario) => scenario.disposition === "adopted").surfaceBindings = [];
  await assert.rejects(
    validateEraSituationLedger(ledger),
    /Adopted scenario lacks a game-surface binding/
  );
});

test("Era situation ledger rejects deferred scenarios entering public output", async () => {
  const ledger = clone(await loadEraSituationLedger());
  ledger.scenarios.find((scenario) => scenario.disposition === "deferred")
    .deploymentProfiles.push("public-playtest");
  await assert.rejects(
    validateEraSituationLedger(ledger),
    /Deferred scenario enters public-playtest/
  );
});

test("Era situation ledger rejects deployed cards missing from traceability", async () => {
  const ledger = clone(await loadEraSituationLedger());
  const scenario = ledger.scenarios.find((entry) =>
    entry.surfaceBindings.some((binding) => binding.surfaceId === "headline:ten_dollar_intelligence")
  );
  scenario.surfaceBindings = scenario.surfaceBindings.filter(
    (binding) => binding.surfaceId !== "headline:ten_dollar_intelligence"
  );
  await assert.rejects(
    validateEraSituationLedger(ledger),
    /Deployed game surfaces absent from the Era ledger: headline:ten_dollar_intelligence/
  );
});

test("public deployment profile excludes internal and deferred material", async () => {
  const ledger = await loadEraSituationLedger();
  const profile = ledger.deploymentProfiles["public-playtest"];
  assert.equal(profile.deployable, true);
  assert.equal(profile.accessControlled, false);
  assert.deepEqual(profile.galleries, ["baseline"]);
  assert.ok(!profile.interfaces.includes("simulation-lab"));
  assert.ok(!profile.documents.includes("*"));
  assert.ok(!profile.runtimeArtifacts.includes("*"));
  assert.ok(profile.runtimeArtifacts.includes("dist/runtime/escalations.json"));
  assert.ok(profile.runtimeArtifacts.includes("dist/runtime/simulation-copy.json"));
  assert.ok(!profile.runtimeArtifacts.includes("dist/runtime/tactics.json"));
  assert.ok(!profile.runtimeArtifacts.includes("dist/runtime/secret-objectives.json"));
  for (const scenario of ledger.scenarios.filter((entry) =>
    ["deferred", "research-backlog"].includes(entry.disposition)
  )) {
    assert.ok(!scenario.deploymentProfiles.includes("public-playtest"), scenario.id);
  }
});

test("public deployment profile must close over browser imports and runtime data", async () => {
  const missingRuntime = clone(await loadEraSituationLedger());
  missingRuntime.deploymentProfiles["public-playtest"].runtimeArtifacts =
    missingRuntime.deploymentProfiles["public-playtest"].runtimeArtifacts.filter(
      (target) => target !== "dist/runtime/simulation-copy.json"
    );
  await assert.rejects(
    validateEraSituationLedger(missingRuntime),
    /omits runtime dependencies: dist\/runtime\/simulation-copy\.json/
  );

  const missingModule = clone(await loadEraSituationLedger());
  missingModule.deploymentProfiles["public-playtest"].labModules =
    missingModule.deploymentProfiles["public-playtest"].labModules.filter(
      (target) => target !== "environment/core-economy-match.js"
    );
  await assert.rejects(
    validateEraSituationLedger(missingModule),
    /omits imported lab module environment\/core-economy-match\.js/
  );
});
