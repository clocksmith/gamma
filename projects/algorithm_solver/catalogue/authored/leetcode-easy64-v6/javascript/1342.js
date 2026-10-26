'use strict';

// 1342. Number of Steps to Reduce a Number to Zero (Easy).
// Specification: https://leetcode.com/problems/number-of-steps-to-reduce-a-number-to-zero/description/
// O(log(num + 1)) time, O(1) space; use integer arithmetic.
function solve(num) {
  let remaining = num;
  let result = 0;
  while (remaining > 0) {
    remaining = remaining % 2 === 0 ? remaining / 2 : remaining - 1;
    result++;
  }
  return result;
}

const numberOfSteps = solve;
class Solution {
  numberOfSteps(num) { return solve(num); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfSteps };
