'use strict';

// 910. Smallest Range II (Medium).
// Specification: https://leetcode.com/problems/smallest-range-ii/description/
function solve(nums, k) {
  const sorted = nums.slice().sort((a, b) => a - b);
  let best = sorted[sorted.length - 1] - sorted[0];
  for (let i = 0; i < sorted.length - 1; i++) {
    const low = Math.min(sorted[0] + k, sorted[i + 1] - k);
    const high = Math.max(sorted[sorted.length - 1] - k, sorted[i] + k);
    best = Math.min(best, high - low);
  }
  return best;
}
const smallestRangeII = solve;
class Solution { smallestRangeII(nums, k) { return solve(nums, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestRangeII };
