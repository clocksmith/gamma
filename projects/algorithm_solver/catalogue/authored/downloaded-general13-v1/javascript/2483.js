'use strict';

// 2483. Minimum Penalty for a Shop (Medium).
// Specification: https://leetcode.com/problems/minimum-penalty-for-a-shop/description/
function solve(customers) {
  let totalY = 0;
  for (const ch of customers) if (ch === 'Y') totalY++;
  let prefixN = 0, suffixY = totalY, best = 0, bestPen = Infinity;
  for (let j = 0; j <= customers.length; j++) {
    const pen = prefixN + suffixY;
    if (pen < bestPen) { bestPen = pen; best = j; }
    if (j < customers.length) {
      if (customers[j] === 'N') prefixN++; else suffixY--;
    }
  }
  return best;
}
const bestClosingTime = solve;
class Solution { bestClosingTime(customers) { return solve(customers); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, bestClosingTime };
