'use strict';

// 3641. Longest Semi-Repeating Subarray.
// Specification: https://leetcode.com/problems/longest-semi-repeating-subarray/description/
// Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
// O(n) expected time and space; count distinct values occurring at least twice, not duplicate positions.
// Inputs are not modified.

function solve(nums, k) {
  const counts = new Map();
  let repeated = 0, left = 0, best = 0;
  for (let right = 0; right < nums.length; right++) {
    const value = nums[right], count = (counts.get(value) || 0) + 1;
    counts.set(value, count);
    if (count === 2) repeated++;
    while (repeated > k) {
      const outgoing = nums[left++], previous = counts.get(outgoing);
      if (previous === 2) repeated--;
      counts.set(outgoing, previous - 1);
    }
    best = Math.max(best, right - left + 1);
  }
  return best;
}

const longestSubarray = solve;
class Solution {
  longestSubarray(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestSubarray };
