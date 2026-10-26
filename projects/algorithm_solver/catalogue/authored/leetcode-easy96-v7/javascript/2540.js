'use strict';

// 2540. Minimum Common Value (Easy).
// Specification: https://leetcode.com/problems/minimum-common-value/description/
// O(n + m) time, O(1) space; advance the smaller sorted value; preserve both arrays.
function solve(nums1, nums2) {
  let first = 0;
  let second = 0;
  while (first < nums1.length && second < nums2.length) {
    if (nums1[first] === nums2[second]) return nums1[first];
    if (nums1[first] < nums2[second]) first++;
    else second++;
  }
  return -1;
}

const getCommon = solve;
class Solution {
  getCommon(nums1, nums2) { return solve(nums1, nums2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getCommon };
