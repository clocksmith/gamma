'use strict';

// 2215. Find the Difference of Two Arrays (Easy).
// Specification: https://leetcode.com/problems/find-the-difference-of-two-arrays/description/
// O(n + m) expected time and space; distinct results in first-occurrence order; preserve inputs.
function solve(nums1, nums2) {
  const first = new Set(nums1);
  const second = new Set(nums2);
  const firstOnly = [];
  const secondOnly = [];
  for (const value of first) {
    if (!second.has(value)) firstOnly.push(value);
  }
  for (const value of second) {
    if (!first.has(value)) secondOnly.push(value);
  }
  return [firstOnly, secondOnly];
}

const findDifference = solve;
class Solution {
  findDifference(nums1, nums2) { return solve(nums1, nums2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findDifference };
