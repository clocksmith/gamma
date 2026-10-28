'use strict';

// 795. Number of Subarrays with Bounded Maximum (Medium).
// Specification: https://leetcode.com/problems/number-of-subarrays-with-bounded-maximum/description/
function countAtMost(nums, bound) {
  let total = 0; let current = 0;
  for (const value of nums) {
    if (value <= bound) { current++; total += current; }
    else current = 0;
  }
  return total;
}
function solve(nums, left, right) { return countAtMost(nums, right) - countAtMost(nums, left - 1); }
const numSubarrayBoundedMax = solve;
class Solution { numSubarrayBoundedMax(nums, left, right) { return solve(nums, left, right); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numSubarrayBoundedMax };
