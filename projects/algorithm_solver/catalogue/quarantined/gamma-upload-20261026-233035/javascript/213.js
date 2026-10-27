'use strict';
// 213. House Robber II.
function linear(nums, start, end) {
  let previous = 0; let current = 0;
  for (let index = start; index < end; index += 1) [previous, current] = [current, Math.max(current, previous + nums[index])];
  return current;
}
function solve(nums) {
  return nums.length === 1 ? nums[0] : Math.max(linear(nums, 0, nums.length - 1), linear(nums, 1, nums.length));
}
const rob = solve;
class Solution { rob(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, rob };
