'use strict';

// 3381. Maximum Subarray Sum With Length Divisible by K (Medium).
// Specification: https://leetcode.com/problems/maximum-subarray-sum-with-length-divisible-by-k/description/
function solve(nums, k) {
  const minPrefix = Array(k).fill(Infinity);
  minPrefix[k - 1] = 0;
  let prefix = 0; let ans = -Infinity;
  for (let i = 0; i < nums.length; i++) {
    prefix += nums[i];
    ans = Math.max(ans, prefix - minPrefix[i % k]);
    minPrefix[i % k] = Math.min(minPrefix[i % k], prefix);
  }
  return ans;
}
const maxSubarraySum = solve;
class Solution { maxSubarraySum(nums, k) { return solve(nums, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSubarraySum };
