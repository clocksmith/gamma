'use strict';

// 713. Subarray Product Less Than K (Medium).
// Specification: https://leetcode.com/problems/subarray-product-less-than-k/description/
function solve(nums, k) {
  if (k <= 1) return 0;
  let product = 1; let left = 0; let count = 0;
  for (let right = 0; right < nums.length; right++) {
    product *= nums[right];
    while (product >= k) { product /= nums[left]; left++; }
    count += right - left + 1;
  }
  return count;
}
const numSubarrayProductLessThanK = solve;
class Solution { numSubarrayProductLessThanK(nums, k) { return solve(nums, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numSubarrayProductLessThanK };
