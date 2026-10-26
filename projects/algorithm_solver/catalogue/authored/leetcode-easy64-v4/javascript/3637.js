'use strict';

// 3637. Trionic Array I (Easy).
// Specification: https://leetcode.com/problems/trionic-array-i/description/
// O(n) time, O(1) space; each of the three strict runs needs at least one edge.
function solve(nums) {
  const length = nums.length;
  let index = 1;
  while (index < length && nums[index] > nums[index - 1]) index++;
  if (index === 1 || index === length) return false;
  const firstTurn = index;
  while (index < length && nums[index] < nums[index - 1]) index++;
  if (index === firstTurn || index === length) return false;
  const secondTurn = index;
  while (index < length && nums[index] > nums[index - 1]) index++;
  return index === length && index > secondTurn;
}

const isTrionic = solve;
class Solution {
  isTrionic(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isTrionic };
