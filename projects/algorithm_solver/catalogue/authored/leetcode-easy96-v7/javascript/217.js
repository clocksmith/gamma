'use strict';

// 217. Contains Duplicate (Easy).
// Specification: https://leetcode.com/problems/contains-duplicate/description/
// O(n) expected time, O(n) space; preserve nums.
function solve(nums) {
  const seen = new Set();
  for (const value of nums) {
    if (seen.has(value)) return true;
    seen.add(value);
  }
  return false;
}

const containsDuplicate = solve;
class Solution {
  containsDuplicate(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, containsDuplicate };
