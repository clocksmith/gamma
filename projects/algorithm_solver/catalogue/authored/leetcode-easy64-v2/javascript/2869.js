'use strict';

// 2869. Minimum Operations to Collect Elements (Easy).
// Specification: https://leetcode.com/problems/minimum-operations-to-collect-elements/description/
// O(n) expected time, O(k) space; inspect the suffix without removing input elements.
function solve(nums, k) {
  const collected = new Set();
  for (let index = nums.length - 1; index >= 0; index--) {
    const value = nums[index];
    if (value >= 1 && value <= k) collected.add(value);
    if (collected.size === k) return nums.length - index;
  }
  return -1;
}

const minOperations = solve;
class Solution {
  minOperations(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
