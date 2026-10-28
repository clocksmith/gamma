'use strict';

// 3364. Minimum Positive Sum Subarray (Easy).
// Specification: https://leetcode.com/problems/minimum-positive-sum-subarray/description/
function solve(nums, l, r) {
  let best = Infinity;
  for (let i = 0; i < nums.length; i++) {
    let sum = 0;
    for (let j = i; j < nums.length && j - i + 1 <= r; j++) {
      sum += nums[j];
      const len = j - i + 1;
      if (len >= l && sum > 0) best = Math.min(best, sum);
    }
  }
  return best === Infinity ? -1 : best;
}
const minimumSumSubarray = solve;
class Solution { minimumSumSubarray(nums, l, r) { return solve(nums, l, r); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumSumSubarray };
