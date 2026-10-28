'use strict';

// 1846. Maximum Element After Decreasing and Rearranging (Medium).
// Specification: https://leetcode.com/problems/maximum-element-after-decreasing-and-rearranging/description/
function solve(arr) {
  const sorted = arr.slice().sort((a, b) => a - b);
  sorted[0] = 1;
  for (let i = 1; i < sorted.length; i++) {
    if (sorted[i] > sorted[i - 1] + 1) sorted[i] = sorted[i - 1] + 1;
  }
  return sorted[sorted.length - 1];
}
const maximumElementAfterDecrementingAndRearranging = solve;
class Solution { maximumElementAfterDecrementingAndRearranging(arr) { return solve(arr); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumElementAfterDecrementingAndRearranging };
