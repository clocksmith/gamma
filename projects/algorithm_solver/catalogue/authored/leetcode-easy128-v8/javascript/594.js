'use strict';

// 594. Longest Harmonious Subsequence (Easy).
// Specification: https://leetcode.com/problems/longest-harmonious-subsequence/description/
// O(n) expected time, O(n) space; combine frequencies only for values differing by one.
function solve(nums) {
  const counts = new Map();
  for (const value of nums) counts.set(value, (counts.get(value) || 0) + 1);
  let longest = 0;
  for (const [value, count] of counts) {
    if (counts.has(value + 1)) longest = Math.max(longest, count + counts.get(value + 1));
  }
  return longest;
}

const findLHS = solve;
class Solution {
  findLHS(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findLHS };
