"use strict";
// Hack2Hire 697460b3a0697bac5fdca97e (Distinct Wall Crossing on Number Line) over an INFERRED spec; qualification unknown.

function bestFor(first, second, energy) {
  // first side is crossed twice (there and back), second side once
  let best = 0;
  let j = second.length - 1;
  for (let i = 0; i < first.length; i++) {
    if (2 * first[i] > energy) break;
    while (j > 0 && 2 * first[i] + second[j] > energy) j--;
    best = Math.max(best, i + j);
  }
  return best;
}

function solve(energy, positions, costs) {
  const right = [], left = [];
  for (let i = 0; i < positions.length; i++) {
    if (positions[i] > 0) right.push([positions[i], costs[i]]);
    else left.push([-positions[i], costs[i]]);
  }
  right.sort((x, y) => x[0] - y[0]);
  left.sort((x, y) => x[0] - y[0]);
  const pr = [0];
  for (const [, c] of right) pr.push(pr[pr.length - 1] + c);
  const pl = [0];
  for (const [, c] of left) pl.push(pl[pl.length - 1] + c);
  return Math.max(bestFor(pr, pl, energy), bestFor(pl, pr, energy));
}

function maxDistinctWalls(energy, positions, costs) { return solve(energy, positions, costs); }

module.exports = solve;
module.exports.maxDistinctWalls = maxDistinctWalls;
