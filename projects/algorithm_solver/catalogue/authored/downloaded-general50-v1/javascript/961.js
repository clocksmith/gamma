'use strict';

// 961. N-Repeated Element in Size 2N Array (Easy).
// Specification: https://leetcode.com/problems/n-repeated-element-in-size-2n-array/description/
function solve(nums) {
  const counts = new Map();
  let best = nums[0]; let bestCount = 0;
  for (const v of nums) {
    const c = (counts.get(v) || 0) + 1;
    counts.set(v, c);
    if (c > bestCount) { bestCount = c; best = v; }
  }
  return best;
}
const repeatedNTimes = solve;
class Solution { repeatedNTimes(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, repeatedNTimes };
