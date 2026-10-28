'use strict';

// 1874. Minimize Product Sum of Two Arrays (Medium).
// Specification: https://leetcode.com/problems/minimize-product-sum-of-two-arrays/description/
function solve(nums1, nums2) {
  const ascending = nums1.slice().sort((a, b) => a - b);
  const descending = nums2.slice().sort((a, b) => b - a);
  let total = 0;
  for (let i = 0; i < ascending.length; i++) total += ascending[i] * descending[i];
  return total;
}
const minProductSum = solve;
class Solution { minProductSum(nums1, nums2) { return solve(nums1, nums2); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minProductSum };
