'use strict';

// 2670. Find the Distinct Difference Array (Easy).
// Specification: https://leetcode.com/problems/find-the-distinct-difference-array/description/
// O(n) expected time, O(n) space; maintain prefix membership and remaining suffix frequencies.
function solve(nums) {
  const suffix = new Map();
  for (const value of nums) suffix.set(value, (suffix.get(value) || 0) + 1);
  const prefix = new Set();
  const result = [];
  for (const value of nums) {
    prefix.add(value);
    const remaining = suffix.get(value) - 1;
    if (remaining === 0) suffix.delete(value);
    else suffix.set(value, remaining);
    result.push(prefix.size - suffix.size);
  }
  return result;
}

const distinctDifferenceArray = solve;
class Solution {
  distinctDifferenceArray(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, distinctDifferenceArray };
