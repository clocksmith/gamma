'use strict';

// 2099. Find Subsequence of Length K With the Largest Sum (Easy).
// Specification: https://leetcode.com/problems/find-subsequence-of-length-k-with-the-largest-sum/description/
// O(n log n) time, O(n) space; select by value, break ties by index, then restore input order.
function solve(nums, k) {
  const order = Array.from({ length: nums.length }, (_, index) => index);
  order.sort((a, b) => nums[b] - nums[a] || a - b);
  const selected = order.slice(0, k).sort((a, b) => a - b);
  return selected.map(index => nums[index]);
}

const maxSubsequence = solve;
class Solution {
  maxSubsequence(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSubsequence };
