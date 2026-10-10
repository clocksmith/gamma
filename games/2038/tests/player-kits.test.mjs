import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";
import { resolvePlayerKits } from "../lab/rules/player-kits.js";
import { displayPlayerKit } from "../lab/contracts/report-migrations.js";
import { createInteractiveGame } from "../lab/runtime/create-interactive-game.js";
import { createPlayerPolicy } from "../lab/policies/policy-factory.js";
const json = async name => JSON.parse(await readFile(new URL(`../dist/runtime/${name}.json`, import.meta.url), "utf8"));
const config = await json("game-config");
const factions = await json("factions");
const headlines = await json("headlines");
const ids = config.playerKits.map(kit => kit.id);
function mechanical(value) {
  if (Array.isArray(value)) return value.map(mechanical);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(Object.entries(value).filter(([key]) => key !== "kitId").map(([key, item]) => [key, mechanical(item)]));
}
test("six faction identities accept every equipment kit without changing starts, abilities or ownership", async () => {
  for (const faction of factions.factions) for (const kitId of ids) {
    const assignments = [kitId, ...ids.filter(id => id !== kitId).slice(0, 3)];
    const { match } = await createInteractiveGame({ factionId: faction.id, kitAssignments: assignments, seed: "kits" });
    assert.equal(match.players[0].kitId, kitId);
    assert.equal(match.players[0].factionId, faction.id);
    for (const key of ["runway", "compute", "capability", "customers", "reputation"]) assert.equal(match.players[0][key], faction.starts[key]);
    assert.deepEqual(match.factions[0].abilities, faction.abilities);
    assert.equal(new Set(match.players.flatMap(p => p.pieces.map(piece => piece.id))).size, 8);

  }
});
test("invalid, duplicate and incorrectly sized assignments fail before a game starts", () => {
  for (const assignments of [[ids[0], ids[0]], ["unknown", ids[1]], [ids[0]], null]) assert.throws(() => resolvePlayerKits(config, 2, assignments));
});
test("kit permutations preserve complete decisions, production, Audit, scores and endings", async () => {
  for (const count of [2,3,4,5]) {
    let reference;
    for (const offset of [0, 1, 3]) {
      const kitAssignments = Array.from({length:count}, (_, seat) => ids[(seat + offset) % ids.length]);
      const {match} = await createInteractiveGame({playerCount:count, kitAssignments, seed:`kit-proof-${count}`});
      // Use a deterministic legal-choice policy so every emitted packet is compared,
      // including Audit and all state-changing resolutions.
      const packets = [];
      const fixture = {async decide(packet) { packets.push(mechanical(packet)); return {decision: {decisionId:packet.legalDecisions[0].decisionId, rationale:"kit equivalence"}, receipt:{provider:"fixture"}}; }};
      const result = await match.play(Array.from({length:count}, () => fixture));
      const observed = mechanical({packets, result});
      if (reference) assert.deepEqual(observed, reference);
      else reference = observed;
    }
  }
});
test("historical display fallback does not mutate a retained report", () => {
  const player = Object.freeze({seat:2, factionId:"foundry", objectiveRecord:{kind:"old",value:9}});
  assert.equal(displayPlayerKit(config, player).id, ids[2]);
  assert.equal(player.kitId, undefined);
  assert.equal(displayPlayerKit(config, {...player,kitId:ids[4]}).id, ids[4]);
});

test("unchanged weighted policies choose identical actions under kit permutations", async () => {
  const profiles = (await json("player-strategies")).profiles;
  for (const count of [3,4,5]) {
    let reference;
    for (const offset of [0,2]) {
      const {match} = await createInteractiveGame({playerCount:count,kitAssignments:ids.slice(offset).concat(ids.slice(0,offset)).slice(0,count), seed:`weighted-kits-${count}`});
      const policies = match.players.map((_,seat) => createPlayerPolicy(profiles[seat % profiles.length], "weighted"));
      const observed = mechanical(await match.play(policies));
      if (reference) assert.deepEqual(observed, reference); else reference=observed;
    }
  }
});
