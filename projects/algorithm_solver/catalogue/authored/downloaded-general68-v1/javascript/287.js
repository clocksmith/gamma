'use strict';

// 287. Find the Duplicate Number (Medium).
// Specification: https://leetcode.com/problems/find-the-duplicate-number/description/
function solve(nums) {
  const seen = new Set();
  for (const value of nums) { if (seen.has(value)) return value; seen.add(value); }
  return -1;
}
const findDuplicate = solve;
class Solution { findDuplicate(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findDuplicate };
