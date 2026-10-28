'use strict';

// 213. House Robber II (Medium).
// Specification: https://leetcode.com/problems/house-robber-ii/description/
function robLinear(nums) {
  let previous = 0; let current = 0;
  for (const value of nums) { const next = Math.max(current, previous + value); previous = current; current = next; }
  return current;
}
function solve(nums) {
  if (nums.length === 1) return nums[0];
  return Math.max(robLinear(nums.slice(0, -1)), robLinear(nums.slice(1)));
}
const rob = solve;
class Solution { rob(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, rob };
