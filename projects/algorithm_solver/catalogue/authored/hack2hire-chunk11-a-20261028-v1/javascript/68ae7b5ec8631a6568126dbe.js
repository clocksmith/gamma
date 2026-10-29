"use strict";
// Hack2Hire 68ae7b5ec8631a6568126dbe (Find Minimum Score Threshold) over an INFERRED spec; qualification unknown.

function solve(games, threshold) {
  const total = new Map(), lose = new Map();
  for (const [score, result] of games) {
    const v = Number(score);
    total.set(v, (total.get(v) || 0) + 1);
    if (result === "lose") lose.set(v, (lose.get(v) || 0) + 1);
  }
  let best = -1, seen = 0, lost = 0;
  for (const v of [...total.keys()].sort((a, b) => b - a)) {
    seen += total.get(v);
    lost += lose.get(v) || 0;
    if (lost / seen >= threshold) best = v; // IEEE double quotient, identical in both languages
  }
  return best;
}

function findMinimumScoreThreshold(games, threshold) { return solve(games, threshold); }

module.exports = solve;
module.exports.findMinimumScoreThreshold = findMinimumScoreThreshold;
