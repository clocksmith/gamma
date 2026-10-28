'use strict';

// 88. Merge Sorted Array (Easy).
// Specification: https://leetcode.com/problems/merge-sorted-array/description/
function solve(nums1, m, nums2, n) {
  return nums1.slice(0, m).concat(nums2.slice(0, n)).sort((a, b) => a - b);
}
const merge = solve;
class Solution { merge(nums1, m, nums2, n) { return solve(nums1, m, nums2, n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, merge };
