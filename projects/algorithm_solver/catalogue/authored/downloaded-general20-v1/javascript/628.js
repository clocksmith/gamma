'use strict';

// 628. Maximum Product of Three Numbers (Easy).
// Specification: https://leetcode.com/problems/maximum-product-of-three-numbers/description/
function solve(nums) {
  const sorted = nums.slice().sort((a, b) => a - b);
  const n = sorted.length;
  return Math.max(sorted[n - 1] * sorted[n - 2] * sorted[n - 3], sorted[0] * sorted[1] * sorted[n - 1]);
}

const maximumProduct = solve;
class Solution {
  maximumProduct(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumProduct };
