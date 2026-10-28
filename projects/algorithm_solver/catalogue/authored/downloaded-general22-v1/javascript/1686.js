'use strict';

// 1686. Stone Game VI (Medium).
// Specification: https://leetcode.com/problems/stone-game-vi/description/
function solve(aliceValues, bobValues) {
  const order = aliceValues.map((_, i) => i).sort((a, b) => (aliceValues[b] + bobValues[b]) - (aliceValues[a] + bobValues[a]));
  let alice = 0; let bob = 0;
  for (let turn = 0; turn < order.length; turn++) {
    if (turn % 2 === 0) alice += aliceValues[order[turn]];
    else bob += bobValues[order[turn]];
  }
  if (alice > bob) return 1;
  if (alice < bob) return -1;
  return 0;
}
const stoneGameVI = solve;
class Solution { stoneGameVI(aliceValues, bobValues) { return solve(aliceValues, bobValues); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, stoneGameVI };
