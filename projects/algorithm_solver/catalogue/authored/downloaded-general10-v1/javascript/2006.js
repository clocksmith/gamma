'use strict';

// 2006. Count Number of Pairs With Absolute Difference K (Easy).
// Specification: https://leetcode.com/problems/count-number-of-pairs-with-absolute-difference-k/description/
function solve(nums, k) {
  const freq = new Map(); let ans = 0;
  for (const x of nums) {
    if (k === 0) ans += freq.get(x) || 0;
    else ans += (freq.get(x - k) || 0) + (freq.get(x + k) || 0);
    freq.set(x, (freq.get(x) || 0) + 1);
  }
  return ans;
}
const countKDifference = solve;
class Solution { countKDifference(nums, k) { return solve(nums, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, countKDifference };
