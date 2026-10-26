'use strict';

// 1636. Sort Array by Increasing Frequency (Easy).
// Specification: https://leetcode.com/problems/sort-array-by-increasing-frequency/description/
// O(n log n) time, O(n) space; ascending frequency, then descending numeric value.
function solve(nums) {
  const counts = new Map();
  for (const value of nums) counts.set(value, (counts.get(value) || 0) + 1);
  return nums.slice().sort((a, b) => counts.get(a) - counts.get(b) || b - a);
}

const frequencySort = solve;
class Solution {
  frequencySort(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, frequencySort };
