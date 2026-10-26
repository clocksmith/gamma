'use strict';

// 2425. Bitwise XOR of All Pairings: cancel values repeated an even number of times across all pairings.
// O(n + m) time and O(1) auxiliary space on the nonnegative 31-bit domain; inputs are read-only.
function solve(nums1, nums2) {
  let answer = 0;
  if (nums2.length % 2) for (const value of nums1) answer ^= value;
  if (nums1.length % 2) for (const value of nums2) answer ^= value;
  return answer;
}

const xorAllNums = solve;
class Solution {
  xorAllNums(nums1, nums2) { return solve(nums1, nums2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, xorAllNums };
