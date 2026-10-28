'use strict';

// 665. Non-decreasing Array (Medium).
// Specification: https://leetcode.com/problems/non-decreasing-array/description/
function solve(nums) {
  const values = nums.slice();
  let modified = 0;
  for (let i = 1; i < values.length; i++) {
    if (values[i] < values[i - 1]) {
      modified++;
      if (modified > 1) return false;
      if (i - 2 < 0 || values[i] >= values[i - 2]) values[i - 1] = values[i];
      else values[i] = values[i - 1];
    }
  }
  return true;
}
const checkPossibility = solve;
class Solution { checkPossibility(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkPossibility };
