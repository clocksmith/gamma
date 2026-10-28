'use strict';

// 1760. Minimum Limit of Balls in a Bag (Medium).
// Specification: https://leetcode.com/problems/minimum-limit-of-balls-in-a-bag/description/
function feasible(nums, maxOperations, limit) {
  let operations = 0;
  for (const value of nums) operations += Math.ceil(value / limit) - 1;
  return operations <= maxOperations;
}
function solve(nums, maxOperations) {
  let left = 1; let right = Math.max(...nums);
  while (left < right) {
    const mid = Math.floor((left + right) / 2);
    if (feasible(nums, maxOperations, mid)) right = mid;
    else left = mid + 1;
  }
  return left;
}
const minimumSize = solve;
class Solution { minimumSize(nums, maxOperations) { return solve(nums, maxOperations); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumSize };
