import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";
import { createInteractiveGame } from "../lab/runtime/create-interactive-game.js";

const read = path => readFile(new URL(`../${path}`, import.meta.url), "utf8");
const headlines = JSON.parse(await read("dist/runtime/headlines.json")).headlines;
async function game() {
  const { match } = await createInteractiveGame({ playerCount: 3, factionId: "coalition_lab", seed: "rules-review" }, () => {});
  match.choose = async (_p, _seat, _stage, choices) => choices.at(-1);
  await match.beginRound([]);
  return match;
}
async function headline(match, id) {
  const card = headlines.find(card => card.id === id);
  match.round = card.round;
  match.cycle = 1;
  await match.beginRound([]);
  match.headlineDecks[match.round][0] = card;
  await match.prepareHeadline([]);
}
function control(match, owners) {
  const governments = match.board.filter(tile => tile.category === "government");
  const frontier = match.board.find(tile => tile.category === "frontier");
  for (const player of match.players) {
    player.runway = 5;
    player.facilities = [];
    for (const piece of player.pieces) piece.tileId = frontier.instanceId;
  }
  for (let i = 0; i < owners.length; i++) {
    if (owners[i] === null) continue;
    const player = match.players[owners[i]];
    player.pieces.find(piece => piece.tileId === frontier.instanceId).tileId = governments[i].instanceId;
  }
  return governments;
}

test("Government rewards reach both district controllers regardless of tile order", async () => {
  for (const id of ["export_controls", "ai_written_law"]) for (const reverse of [false, true]) {
    const match = await game();
    control(match, [0, 1]);
    if (reverse) match.board.reverse();
    await headline(match, id);
    assert.deepEqual(match.players.map(player => player.runway),
      id === "export_controls" ? [6, 6, 5] : [7, 7, 4], `${id}, reverse=${reverse}`);
  }
});

test("two Government districts pay once, while the Chip reward is separate", async () => {
  for (const id of ["export_controls", "ai_written_law"]) {
    const match = await game();
    control(match, [0, 0]);
    const chip = match.board.find(tile => tile.category === "chip");
    match.players[0].facilities.push({ id: "chip-host", tileId: chip.instanceId, category: "chip" });
    await headline(match, id);
    assert.deepEqual(match.players.map(player => player.runway),
      id === "export_controls" ? [7, 5, 5] : [7, 4, 4]);
  }
});

test("contested and empty Government districts pay nobody; Court counts only acceptances", async () => {
  for (const id of ["export_controls", "ai_written_law"]) {
    const match = await game();
    const districts = control(match, [0, null]);
    match.players[1].pieces[0].tileId = districts[0].instanceId;
    await headline(match, id);
    assert.deepEqual(match.players.map(player => player.runway),
      id === "export_controls" ? [5, 5, 5] : [4, 4, 4]);
  }
  const match = await game();
  control(match, [0, 1]);
  match.choose = async (_p, seat, _stage, choices) => seat === 2 ? choices.at(-1) : choices[0];
  await headline(match, "ai_written_law");
  assert.deepEqual(match.players.map(player => player.runway), [6, 6, 4]);
});

test("Trust awards retain their starting marks and never rescore after a loss or Era reset", async () => {
  const match = await game();
  const player = match.players[0];
  assert.equal(player.trust, 3);
  const before = player.mandate;
  assert.ok(player.mandateAwards.some(award => award.id === "trust-2"));
  match.addResource(player, "trust", 1);
  assert.equal(player.mandate, before + 2);
  match.addResource(player, "trust", -1);
  match.round = 2;
  await match.beginRound([]);
  match.addResource(player, "trust", 1);
  assert.equal(player.trust, 4);
  assert.equal(player.mandate, before + 2);
  assert.equal(player.mandateAwards.filter(award => award.id === "trust-4").length, 1);
});

test("Joint Ventures can share Mega-Cluster hosts and repeat a pair up to shared supply", async () => {
  const match = await game();
  match.round = 3;
  await match.beginRound([]);
  const [left, right] = match.players;
  const a = match.board.find(tile => tile.category === "cloud");
  const b = match.board.find(tile => tile.category !== "frontier" && match.areAdjacent(a.instanceId, tile.instanceId));
  left.facilities = [{ id: "left", tileId: a.instanceId, category: a.category }];
  right.facilities = [{ id: "right", tileId: b.instanceId, category: b.category }];
  match.megaClusters = [{ id: "existing-cluster", leadSeat: 0, leftId: "left", rightId: "other-host" }];
  for (let i = 0; i < match.config.sharedSupply.jointVenturePairs; i++) {
    const proposal = match.legalResolutions(0, "influence").find(choice => choice.parameters.mode === "joint_venture");
    assert.ok(proposal, `host remains eligible for venture ${i + 1}`);
    match.choose = async (_p, _seat, _stage, choices) => choices[0];
    assert.equal(await match.negotiate([], 0, proposal), true);
  }
  assert.equal(match.legalResolutions(0, "influence").some(choice => choice.parameters.mode === "joint_venture"), false);
  assert.equal(new Set(match.contracts.map(contract => contract.id)).size, match.config.sharedSupply.jointVenturePairs);
  // Compare identical Production states with and without two active duplicate contracts.
  match.contracts = match.contracts.slice(0, 2);
  match.megaClusters = [];
  const original = match.contracts;
  match.contracts = [];
  for (const player of match.players) { player.runway = 0; player.compute = 0; }
  await match.produceAll([]);
  const baseline = right.compute;
  match.contracts = original;
  for (const player of match.players) { player.runway = 0; player.compute = 0; }
  await match.produceAll([]);
  assert.equal(right.compute, baseline + 2, "each duplicate contract pays the Cloud host icon independently");
});

test("player documents teach actions early and preserve permanent physical state and precise aid rules", async () => {
  const rules = await read("dist/docs/core-rules.md");
  const order = ["## 1. Setup", "## 2. Resources", "## 3. Central loop", "## 4. Core Actions", "## 5. Era sequence", "## 6. Four-Era progression", "## 7. Final scoring", "## Rules Reference"];
  let previous = -1;
  for (const heading of order) {
    const index = rules.indexOf(heading);
    assert.ok(index > previous, heading);
    previous = index;
  }
  assert.doesNotMatch(rules, /Dossier|universal Protection|Safety currency|faction scoring rule|quantum record disputes|Era halves upward/);
  const spec = await read("physical/component-spec.md");
  assert.match(spec, /Trust milestone positions are 0, 2, 4, 6/);
  assert.match(spec, /never moves backward/i);
  const references = JSON.parse(await read("dist/runtime/reference-cards.json")).playerReferences;
  const production = references.find(card => card.id === "production_audit");
  assert.match(production.frontText.join(" "), /faction Production income first/);
  assert.match(production.backText[3], /Runway; if none remains, lose 1 Trust/);
  assert.match(production.backText[3], /both are zero, lose nothing further/);
  const scoring = references.find(card => card.id === "public_mandate");
  assert.match(scoring.backText[5], /Collective Trust.*Setup Collective Trust.*Systemic Risk strictly below player count/);
  assert.match(scoring.backText[6], /The Singularity/);
});
