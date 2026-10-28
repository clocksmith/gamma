'use strict';

// 41. First Missing Positive (Hard).
// Specification: https://leetcode.com/problems/first-missing-positive/description/
function solve(nums) {
  const seen = new Set(nums);
  let value = 1;
  while (seen.has(value)) value++;
  return value;
}
const firstMissingPositive = solve;
class Solution { firstMissingPositive(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, firstMissingPositive };
