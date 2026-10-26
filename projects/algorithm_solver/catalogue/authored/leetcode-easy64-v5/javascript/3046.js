'use strict';

// 3046. Split the Array (Easy).
// Specification: https://leetcode.com/problems/split-the-array/description/
// O(n) expected time, O(n) space; an even-length input is splittable iff each count is at most two.
function solve(nums) {
  const counts = new Map();
  for (const value of nums) {
    const count = (counts.get(value) || 0) + 1;
    if (count > 2) return false;
    counts.set(value, count);
  }
  return true;
}

const isPossibleToSplit = solve;
class Solution {
  isPossibleToSplit(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isPossibleToSplit };
