import assert from "node:assert/strict";
import test from "node:test";
import {
  outcomePlacementPoint,
  outcomeRanks
} from "../lab/balance/outcome-placement.js";

function standing(seat, score, trust = 0, customers = 0, compute = 0) {
  return { seat, score, trust, customers, compute };
}

test("AGI victory outranks higher raw Mandate in matchup evidence", () => {
  const agiWinner = standing(2, 11, 2, 1, 0);
  const mandateLeader = standing(0, 24, 6, 5, 8);
  const outcome = {
    winnerSeats: [2],
    standings: [mandateLeader, standing(1, 18), agiWinner]
  };
  assert.equal(outcomePlacementPoint(outcome, agiWinner, mandateLeader), 1);
  assert.equal(outcomePlacementPoint(outcome, mandateLeader, agiWinner), 0);
  assert.deepEqual(Object.fromEntries(outcomeRanks(outcome)), {
    0: 2,
    1: 3,
    2: 1
  });
});

test("ordinary ties and non-winner tiebreaks retain game placement semantics", () => {
  const tiedWinnerA = standing(0, 20, 4, 2, 1);
  const tiedWinnerB = standing(1, 20, 4, 2, 1);
  const strongerRunnerUp = standing(2, 18, 4, 2, 1);
  const weakerRunnerUp = standing(3, 18, 3, 5, 8);
  const outcome = {
    winnerSeats: [0, 1],
    standings: [tiedWinnerA, tiedWinnerB, strongerRunnerUp, weakerRunnerUp]
  };
  assert.equal(outcomePlacementPoint(outcome, tiedWinnerA, tiedWinnerB), 0.5);
  assert.equal(outcomePlacementPoint(outcome, strongerRunnerUp, weakerRunnerUp), 1);
  assert.deepEqual(Object.fromEntries(outcomeRanks(outcome)), {
    0: 1,
    1: 1,
    2: 3,
    3: 4
  });
});
