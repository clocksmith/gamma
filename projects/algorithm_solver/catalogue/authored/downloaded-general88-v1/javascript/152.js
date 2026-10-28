'use strict';

// 152. Maximum Product Subarray (Medium).
// Specification: https://leetcode.com/problems/maximum-product-subarray/description/
function solve(nums) {
  let best = nums[0]; let maxEnding = nums[0]; let minEnding = nums[0];
  for (let i = 1; i < nums.length; i++) {
    const value = nums[i];
    const candidates = [value, maxEnding * value, minEnding * value];
    maxEnding = Math.max(...candidates);
    minEnding = Math.min(...candidates);
    best = Math.max(best, maxEnding);
  }
  return best;
}
const maxProduct = solve;
class Solution { maxProduct(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxProduct };
