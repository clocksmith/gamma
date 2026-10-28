'use strict';

// 198. House Robber (Medium).
// Specification: https://leetcode.com/problems/house-robber/description/
function solve(nums) {
  let previous = 0; let current = 0;
  for (const value of nums) { const next = Math.max(current, previous + value); previous = current; current = next; }
  return current;
}
const rob = solve;
class Solution { rob(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, rob };
