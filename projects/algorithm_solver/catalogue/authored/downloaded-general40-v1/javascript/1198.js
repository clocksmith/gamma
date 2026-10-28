'use strict';

// 1198. Find Smallest Common Element in All Rows (Medium).
// Specification: https://leetcode.com/problems/find-smallest-common-element-in-all-rows/description/
function solve(mat) {
  const counts = new Map();
  for (const row of mat) {
    for (const value of new Set(row)) counts.set(value, (counts.get(value) || 0) + 1);
  }
  let best = Infinity;
  for (const [value, count] of counts) { if (count === mat.length) best = Math.min(best, value); }
  return best === Infinity ? -1 : best;
}
const smallestCommonElement = solve;
class Solution { smallestCommonElement(mat) { return solve(mat); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestCommonElement };
