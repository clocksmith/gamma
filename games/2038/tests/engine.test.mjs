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
test("six unique action areas have fixed layout independent of seed or geometry", () => {
  const a = generateBoard(config, "one"),
    b = generateBoard(config, "two");
  assert.deepEqual(a, b);
  assert.deepEqual(
    a.map((a) => a.actionId),
    config.actions.map((a) => a.id),
  );
  assert.equal(a.length, 6);
  assert.ok(
    a.every((a) => a.facilitySpaces === 2 && !("q" in a) && !("r" in a)),
  );
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
test("numeric resource state is exactly four tracks; Customers derive from cards", () => {
  const m = fixture();
  assert.deepEqual(Object.keys(config.resources), [
    "runway",
    "compute",
    "capability",
    "reputation",
  ]);
  const p = m.players[0];
  const n = p.customers;
  m.gainCustomer(p);
  assert.equal(p.customers, n + 1);
  assert.equal(p.customerCards.length, p.customers);
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
