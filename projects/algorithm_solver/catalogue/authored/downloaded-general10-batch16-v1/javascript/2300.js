'use strict';

// 2300. Successful Pairs of Spells and Potions (Medium).
// Specification: https://leetcode.com/problems/successful-pairs-of-spells-and-potions/description/
function solve(spells, potions, success) {
  const sorted = potions.slice().sort((a, b) => a - b);
  const out = [];
  for (const spell of spells) {
    const need = Math.ceil(success / spell);
    let lo = 0; let hi = sorted.length;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (sorted[mid] < need) lo = mid + 1; else hi = mid;
    }
    out.push(sorted.length - lo);
  }
  return out;
}
const successfulPairs = solve;
class Solution { successfulPairs(spells, potions, success) { return solve(spells, potions, success); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, successfulPairs };
