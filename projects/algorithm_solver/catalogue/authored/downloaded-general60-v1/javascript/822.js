'use strict';

// 822. Card Flipping Game (Medium).
// Specification: https://leetcode.com/problems/card-flipping-game/description/
function solve(fronts, backs) {
  const bad = new Set();
  for (let i = 0; i < fronts.length; i++) { if (fronts[i] === backs[i]) bad.add(fronts[i]); }
  let best = Infinity;
  for (const value of fronts.concat(backs)) { if (!bad.has(value)) best = Math.min(best, value); }
  return best === Infinity ? 0 : best;
}
const flipgame = solve;
class Solution { flipgame(fronts, backs) { return solve(fronts, backs); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, flipgame };
