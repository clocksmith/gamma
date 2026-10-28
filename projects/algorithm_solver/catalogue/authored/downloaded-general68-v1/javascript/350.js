'use strict';

// 350. Intersection of Two Arrays II (Easy).
// Specification: https://leetcode.com/problems/intersection-of-two-arrays-ii/description/
function solve(nums1, nums2) {
  const counts = new Map();
  for (const value of nums1) counts.set(value, (counts.get(value) || 0) + 1);
  const result = [];
  for (const value of nums2) {
    if ((counts.get(value) || 0) > 0) { result.push(value); counts.set(value, counts.get(value) - 1); }
  }
  return result.sort((a, b) => a - b);
}
const intersect = solve;
class Solution { intersect(nums1, nums2) { return solve(nums1, nums2); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, intersect };
