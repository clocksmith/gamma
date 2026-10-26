'use strict';

// 2032. Two Out of Three (Easy).
// Specification: https://leetcode.com/problems/two-out-of-three/description/
// O(total input length + 100) time, O(1) bounded-domain space besides the result; preserve inputs.
function solve(nums1, nums2, nums3) {
  const membership = new Array(101).fill(0);
  for (const value of nums1) membership[value] |= 1;
  for (const value of nums2) membership[value] |= 2;
  for (const value of nums3) membership[value] |= 4;
  const result = [];
  for (let value = 1; value <= 100; value++) {
    const mask = membership[value];
    if ((mask & (mask - 1)) !== 0) result.push(value);
  }
  return result;
}

const twoOutOfThree = solve;
class Solution {
  twoOutOfThree(nums1, nums2, nums3) { return solve(nums1, nums2, nums3); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, twoOutOfThree };
