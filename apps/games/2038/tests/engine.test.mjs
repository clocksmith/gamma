import assert from "node:assert/strict";
import test from "node:test";
import {
  generateBoard,
  createRng,
  shuffle,
  buildTrainingDeck,
  simulateTrainingRun,
} from "../web/src/engine.js";
import { config, fixture } from "./helpers/smaller-game.mjs";
test("eighteen playable hexes surround the Era center and share six Actions", () => {
  const a = generateBoard(config, "one");
  assert.deepEqual(a, generateBoard(config, "two"));
  assert.equal(a.length, 18);
  assert.equal(new Set(a.map(h => `${h.q},${h.r}`)).size, 18);
  assert.ok(a.every(h => h.q !== 0 || h.r !== 0));
  for (const action of config.actions) assert.equal(a.filter(h => h.actionId === action.id).length, 3);
  a[0].yield.amount = 999;
  assert.equal(config.board.tiles[0].yield.amount, 2);
});
test("RNG and shuffle remain deterministic without mutating inputs", () => {
  const a = [1, 2, 3, 4, 5];
  assert.deepEqual(
    shuffle(a, createRng("same")),
    shuffle(a, createRng("same")),
  );
  assert.deepEqual(a, [1, 2, 3, 4, 5]);
});
test("shared Training deck retains forty cards and every face multiplicity", () => {
  const deck = buildTrainingDeck(config, "deck");
  assert.equal(deck.length, 40);
  assert.equal(new Set(deck.map((c) => c.id)).size, 40);
  for (const c of config.trainingDeck.cards)
    assert.equal(deck.filter((d) => d.type === c.id).length, c.count);
});
test("pure Research simulation retains Reputation effects through duplicate crash", () => {
  const deck = [
    { type: "benchmark_leak", kind: "special" },
    { type: "code", kind: "domain" },
    { type: "code", kind: "domain" },
  ];
  const r = simulateTrainingRun(config, "risk", { deck, stopAt: 99 });
  assert.equal(r.capability, 0);
  assert.equal(r.reputation, -1);
  assert.equal(r.outcome, "crashed");
});
test("numeric resource state is five tracks; Mandate is derived", () => {
  const m = fixture();
  assert.deepEqual(Object.keys(config.resources), [
    "runway",
    "compute",
    "capability",
    "reputation",
    "customers",
  ]);
  const p = m.players[0];
  const n = p.customers;
  m.gainCustomer(p);
  assert.equal(p.customers, n + 1);
  assert.equal(p.customerCards, undefined);
  for (const key of [
    "trust",
    "scrutiny",
    "power",
    "systemicRisk",
    "mandate",
    "highestTrustMilestone",
  ])
    assert.equal(p[key], undefined);
});
