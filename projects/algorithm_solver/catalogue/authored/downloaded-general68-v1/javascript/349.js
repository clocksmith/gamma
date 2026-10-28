'use strict';

// 349. Intersection of Two Arrays (Easy).
// Specification: https://leetcode.com/problems/intersection-of-two-arrays/description/
function solve(nums1, nums2) {
  const set2 = new Set(nums2);
  return [...new Set(nums1.filter((value) => set2.has(value)))].sort((a, b) => a - b);
}
const intersection = solve;
class Solution { intersection(nums1, nums2) { return solve(nums1, nums2); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, intersection };
