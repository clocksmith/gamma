'use strict';

// 740. Delete and Earn (Medium).
// Specification: https://leetcode.com/problems/delete-and-earn/description/
function solve(nums) {
  if (nums.length === 0) return 0;
  const maxValue = Math.max(...nums);
  const points = new Array(maxValue + 1).fill(0);
  for (const value of nums) points[value] += value;
  let previous = 0; let current = points[0];
  for (let value = 1; value <= maxValue; value++) { const next = Math.max(current, previous + points[value]); previous = current; current = next; }
  return current;
}
const deleteAndEarn = solve;
class Solution { deleteAndEarn(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, deleteAndEarn };
