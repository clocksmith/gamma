'use strict';

// 2956. Find Common Elements Between Two Arrays (Easy).
// Specification: https://leetcode.com/problems/find-common-elements-between-two-arrays/description/
function solve(nums1, nums2) {
  const set1 = new Set(nums1); const set2 = new Set(nums2);
  let count1 = 0; for (const x of nums1) if (set2.has(x)) count1++;
  let count2 = 0; for (const x of nums2) if (set1.has(x)) count2++;
  return [count1, count2];
}
const findIntersectionValues = solve;
class Solution { findIntersectionValues(nums1, nums2) { return solve(nums1, nums2); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findIntersectionValues };
