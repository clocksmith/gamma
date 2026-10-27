'use strict';

// 3634. Minimum Removals to Balance Array.
// Specification: https://leetcode.com/problems/minimum-removals-to-balance-array/description/
// Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
// O(n log n) time, O(n) space; keep the longest sorted interval with max <= k * min.
// Inputs are not modified.

function solve(nums, k) {
  const ordered = nums.slice().sort((a, b) => a - b);
  let left = 0, longest = 0;
  for (let right = 0; right < ordered.length; right++) {
    while (ordered[right] > ordered[left] * k) left++;
    longest = Math.max(longest, right - left + 1);
  }
  return ordered.length - longest;
}

const minRemoval = solve;
class Solution {
  minRemoval(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minRemoval };
