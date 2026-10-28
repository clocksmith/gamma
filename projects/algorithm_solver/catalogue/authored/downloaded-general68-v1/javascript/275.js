'use strict';

// 275. H-Index II (Medium).
// Specification: https://leetcode.com/problems/h-index-ii/description/
function solve(citations) {
  const n = citations.length;
  let left = 0; let right = n;
  while (left < right) {
    const mid = Math.floor((left + right) / 2);
    if (citations[mid] >= n - mid) right = mid;
    else left = mid + 1;
  }
  return n - left;
}
const hIndex = solve;
class Solution { hIndex(citations) { return solve(citations); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, hIndex };
