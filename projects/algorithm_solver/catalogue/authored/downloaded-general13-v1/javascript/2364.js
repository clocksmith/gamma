'use strict';

// 2364. Count Number of Bad Pairs (Medium).
// Specification: https://leetcode.com/problems/count-number-of-bad-pairs/description/
function solve(nums) {
  const seen = new Map(); let good = 0;
  for (let i = 0; i < nums.length; i++) {
    const key = nums[i] - i;
    good += seen.get(key) || 0;
    seen.set(key, (seen.get(key) || 0) + 1);
  }
  const n = nums.length;
  return n * (n - 1) / 2 - good;
}
const countBadPairs = solve;
class Solution { countBadPairs(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, countBadPairs };
