'use strict';

// 215. Kth Largest Element in an Array (Medium).
// Specification: https://leetcode.com/problems/kth-largest-element-in-an-array/description/
function solve(nums, k) {
  return nums.slice().sort((a, b) => b - a)[k - 1];
}
const findKthLargest = solve;
class Solution { findKthLargest(nums, k) { return solve(nums, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findKthLargest };
