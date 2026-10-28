'use strict';

// 1885. Count Pairs in Two Arrays (Medium).
// Specification: https://leetcode.com/problems/count-pairs-in-two-arrays/description/
function solve(nums1, nums2) {
  const diff = nums1.map((value, i) => value - nums2[i]).sort((a, b) => a - b);
  let count = 0;
  for (let i = 0; i < diff.length; i++) {
    for (let j = i + 1; j < diff.length; j++) { if (diff[i] + diff[j] > 0) count++; }
  }
  return count;
}
const countPairs = solve;
class Solution { countPairs(nums1, nums2) { return solve(nums1, nums2); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPairs };
