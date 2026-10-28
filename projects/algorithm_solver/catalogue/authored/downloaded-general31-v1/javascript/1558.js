'use strict';

// 1558. Minimum Numbers of Function Calls to Make Target Array (Medium).
// Specification: https://leetcode.com/problems/minimum-numbers-of-function-calls-to-make-target-array/description/
function solve(nums) {
  let operations = 0;
  let values = nums.slice();
  while (values.some((v) => v > 0)) {
    let oddCount = 0;
    for (let i = 0; i < values.length; i++) {
      if (values[i] % 2 === 1) { values[i]--; oddCount++; }
    }
    operations += oddCount;
    if (values.some((v) => v > 0)) {
      values = values.map((v) => Math.floor(v / 2));
      operations++;
    }
  }
  return operations;
}
const minOperations = solve;
class Solution { minOperations(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
