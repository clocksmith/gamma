'use strict';

// 2395. Find Subarrays With Equal Sum (Easy).
// Specification: https://leetcode.com/problems/find-subarrays-with-equal-sum/description/
// O(n) expected time, O(n) space; two equal sums of adjacent pairs identify distinct subarrays.
function solve(nums) {
  const seen = new Set();
  for (let index = 1; index < nums.length; index++) {
    const total = nums[index - 1] + nums[index];
    if (seen.has(total)) return true;
    seen.add(total);
  }
  return false;
}

const findSubarrays = solve;
class Solution {
  findSubarrays(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findSubarrays };
