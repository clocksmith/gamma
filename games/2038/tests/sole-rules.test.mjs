import assert from "node:assert/strict";
import { readFile, access, cp, mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import test from "node:test";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { resolve, dirname } from "node:path";
import { createBrowserInteractiveGame } from "../lab/runtime/create-browser-interactive-game.js";
import { createInteractiveGame } from "../lab/runtime/create-interactive-game.js";
import { createGame, commitAction, resolveSelectedAction, locallyEligibleFacilityIds } from "../web/src/engine.js";
import { effectiveRulesVariant } from "../lab/environment/rules-variant.js";

const root = new URL("../", import.meta.url);
const json = async path => JSON.parse(await readFile(new URL(path, root), "utf8"));
const retiredOptions = {
  playProfileId: "advanced-play", moduleIds: ["network-infrastructure"],
  networkInfrastructureEnabled: true, realignmentEnabled: true,
  powerPurchaseRequests: 1, headlinePersistentEffectsEnabled: true,
  headlinePublicProceduresEnabled: true, headlineVolatilityEnabled: true
};

test("both interactive entrypoints reject retired options before any decision", async () => {
  for (const create of [createInteractiveGame, createBrowserInteractiveGame]) {
    for (const [key, value] of Object.entries(retiredOptions)) {
      await assert.rejects(create({rulesVariant: {[key]: value}}, () => {
        assert.fail("invalid setup must not request a decision");
      }), /Unsupported rules option/);
    }
  }
});

test("removed Build choices fail without moving pieces or spending resources", async () => {
  const [config, factions, headlines] = await Promise.all([
    json("dist/runtime/game-config.json"), json("dist/runtime/factions.json"),
    json("dist/runtime/headlines.json")
  ]);
  const state = createGame(config, factions, headlines, "invalid-build", "coalition_lab");
  commitAction(state, "build");
  const before = structuredClone(state);
  assert.throws(() => resolveSelectedAction(config, headlines, state, "agent-1", "frontier-1", {buildMode: "link"}), /Unknown build mode/);
  assert.deepEqual(state, before);
  const {match} = await createInteractiveGame({seed: "invalid-build"}, () => {});
  const snapshot = structuredClone(match.players);
  assert.throws(() => match.applyResolution(0, {actionId: "build", parameters: {buildMode: "link"}}), /Unknown build mode/);
  assert.deepEqual(match.players, snapshot);
});

test("local Power stops at Generator adjacency and retired allocation options fail closed", async () => {
 const board=[0,1,2,3].map(q=>({instanceId:`tile-${q}`,q,r:0}));
 const player={facilities:board.map((tile,i)=>({id:`f${i}`,tileId:tile.instanceId})),generators:[{tileId:"tile-0"}]};
 assert.deepEqual([...locallyEligibleFacilityIds(board,player)].sort(),["f0","f1"]);
 const config=await json("dist/runtime/game-config.json");
 for(const key of ["importedPower","importedFacilityIds","exportedPower","startingGridPower","agiDossier"]) assert.throws(()=>effectiveRulesVariant(config,{[key]:1}),/Unsupported rules option/);
});

test("current projections contain one ruleset and no retired supplement", async () => {
  const graph = await json("content/graph.json");
  for (const {target} of graph.artifacts) {
    const text = await readFile(new URL(target, root), "utf8");
    assert.doesNotMatch(text, /Advanced Play|Default Game|Jurisdictional Realignment|Volatility|playProfileId|playProfiles|networkInfrastructureEnabled|capacity may be sold|in your Network|a Network,|immediate Production trade/, target);
  }
  for (const path of ["advanced.md", ...graph.retiredTargets]) {
    await assert.rejects(access(new URL(path, root)), {code: "ENOENT"});
  }
});


test("the compiler rejects and removes stale supplemental projections in an isolated fixture", async () => {
  const exec = promisify(execFile);
  const fixture = await mkdtemp(new URL("dist/retired-projection-test-", root));
  try {
    const graph = await json("content/graph.json");
    for (const source of [...graph.sourceRoots, "tasks/content/"]) {
      await cp(new URL(source, root), resolve(fixture, source), {recursive: true});
    }
    await exec(process.execPath, ["tasks/content/compile.mjs"], {cwd: fixture});
    for (const target of graph.retiredTargets) {
      const path = resolve(fixture, target);
      await mkdir(dirname(path), {recursive: true});
      await writeFile(path, "Obsolete supplement fixture");
    }
    await assert.rejects(exec(process.execPath, ["tasks/content/compile.mjs", "--check"], {cwd: fixture}), /retired projection/);
    await exec(process.execPath, ["tasks/content/compile.mjs"], {cwd: fixture});
    for (const target of graph.retiredTargets) {
      await assert.rejects(access(resolve(fixture, target)), {code: "ENOENT"});
    }
    await exec(process.execPath, ["tasks/content/compile.mjs", "--check"], {cwd: fixture});
  } finally {
    await rm(fixture, {recursive: true, force: true});
  }
});
