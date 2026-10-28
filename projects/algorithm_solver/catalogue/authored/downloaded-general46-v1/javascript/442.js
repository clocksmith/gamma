'use strict';

// 442. Find All Duplicates in an Array (Medium).
// Specification: https://leetcode.com/problems/find-all-duplicates-in-an-array/description/
function solve(nums) {
  const counts = {};
  const result = [];
  for (const value of nums) counts[value] = (counts[value] || 0) + 1;
  for (const value of Object.keys(counts).map(Number).sort((a, b) => a - b)) { if (counts[value] === 2) result.push(value); }
  return result;
}
const findDuplicates = solve;
class Solution { findDuplicates(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findDuplicates };
