'use strict';

// 413. Arithmetic Slices (Medium).
// Specification: https://leetcode.com/problems/arithmetic-slices/description/
function solve(nums) {
  let total = 0; let run = 0;
  for (let i = 2; i < nums.length; i++) {
    if (nums[i] - nums[i - 1] === nums[i - 1] - nums[i - 2]) { run++; total += run; } else run = 0;
  }
  return total;
}
const numberOfArithmeticSlices = solve;
class Solution { numberOfArithmeticSlices(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfArithmeticSlices };
