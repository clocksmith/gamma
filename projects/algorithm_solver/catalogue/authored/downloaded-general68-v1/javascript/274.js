'use strict';

// 274. H-Index (Medium).
// Specification: https://leetcode.com/problems/h-index/description/
function solve(citations) {
  const sorted = citations.slice().sort((a, b) => b - a);
  let h = 0;
  for (let i = 0; i < sorted.length; i++) { if (sorted[i] >= i + 1) h = i + 1; else break; }
  return h;
}
const hIndex = solve;
class Solution { hIndex(citations) { return solve(citations); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, hIndex };
