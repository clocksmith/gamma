'use strict';

// 3131. Find the Integer Added to Array I (Easy).
// Specification: https://leetcode.com/problems/find-the-integer-added-to-array-i/description/
// O(n) time, O(1) auxiliary space; a valid uniform shift is guaranteed; preserve inputs.
function solve(nums1, nums2) {
  let minimumFirst = nums1[0];
  let minimumSecond = nums2[0];
  for (const value of nums1) minimumFirst = Math.min(minimumFirst, value);
  for (const value of nums2) minimumSecond = Math.min(minimumSecond, value);
  return minimumSecond - minimumFirst;
}

const addedInteger = solve;
class Solution {
  addedInteger(nums1, nums2) { return solve(nums1, nums2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, addedInteger };
