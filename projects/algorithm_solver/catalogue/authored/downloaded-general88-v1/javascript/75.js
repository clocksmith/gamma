'use strict';

// 75. Sort Colors (Medium).
// Specification: https://leetcode.com/problems/sort-colors/description/
function solve(nums) {
  const counts = [0, 0, 0];
  for (const value of nums) counts[value]++;
  const result = [];
  for (let color = 0; color < 3; color++) { for (let i = 0; i < counts[color]; i++) result.push(color); }
  return result;
}
const sortColors = solve;
class Solution { sortColors(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, sortColors };
