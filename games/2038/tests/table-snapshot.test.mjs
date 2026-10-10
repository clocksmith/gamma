import assert from "node:assert/strict";
import test from "node:test";
import { fixture, action, policies, config } from "./helpers/smaller-game.mjs";

test("setup snapshot accounts for every kit piece and hides unrevealed deck order", () => {
  for (const playerCount of [2, 3, 4, 5]) {
    const match = fixture({ playerCount });
    const state = match.snapshot();
    assert.equal(state.board.length, 18);
    assert.equal(state.players.length, playerCount);
    for (const player of state.players) {
      assert.equal(player.pieces.length + player.agentsInSupply, 4);
      assert.equal(
        player.pieces.filter((org) => org.tileId === null).length,
        2,
      );
      for (const key of Object.keys(config.resources))
        assert.equal(player[key], match.factions[player.seat].starts[key] || 0);
    }
    assert.deepEqual(state.trainingDeck, {
      drawCount: 40,
      discardCount: 0,
      topDiscard: null,
    });
    assert.deepEqual(state.revealedHeadlines, []);
    assert.deepEqual(state.revealedMandates, []);
    assert.equal(state.trainingRun, null);
    assert.equal("trainingDrawPile" in state, false);
    assert.equal("eraHeadlines" in state, false);
  }
});

test("visible Training state follows draw, bank, and reshuffle without a second UI ledger", async () => {
  const match = fixture();
  match.trainingDrawPile = [{ id: "code-1", type: "code", kind: "domain" }];
  match.trainingDiscard = [
    { id: "science-1", type: "science", kind: "domain" },
  ];
  let decisions = 0;
  const opponents = policies(match, (packet) => {
    const state = match.snapshot();
    assert.equal(state.trainingRun.seat, 0);
    assert.equal(state.trainingRun.revealed.length, 1);
    assert.equal(
      state.trainingDeck.drawCount + state.trainingDeck.discardCount,
      2,
    );
    assert.equal(
      state.trainingDeck.topDiscard,
      state.trainingRun.revealed.at(-1),
    );
    // Snapshots must not expose writable owned arrays.
    state.trainingRun.revealed.push("fake");
    assert.equal(match.trainingRun.revealed.length, 1);
    decisions++;
    return packet.legalDecisions.find(
      (decision) => decision.decisionId === "research_bank",
    );
  });
  for (let index = 0; index < 2; index++) {
    match.players[0].compute = 2;
    await match.research(opponents, 0, action(match, 0, "research"));
    assert.equal(match.snapshot().trainingRun, null);
  }
  assert.equal(decisions, 2);
  assert.equal(match.trainingShuffle, 1);
});

test("Headline and objective faces become public only when revealed and stay independent", async () => {
  const match = fixture();
  await match.beginRound();
  let state = match.snapshot();
  assert.equal(state.revealedMandates.length, 1);
  assert.equal(state.revealedHeadlines.length, 0);
  await match.prepareHeadline(policies(match));
  state = match.snapshot();
  assert.equal(state.revealedHeadlines.length, 1);
  assert.equal(state.revealedHeadlines[0].id, state.activeHeadline.id);
  state.revealedHeadlines[0].name = "mutated";
  state.revealedMandates[0].name = "mutated";
  assert.notEqual(match.snapshot().revealedHeadlines[0].name, "mutated");
  assert.notEqual(match.snapshot().revealedMandates[0].name, "mutated");
});
