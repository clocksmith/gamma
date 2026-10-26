'use strict';

// 3099. Harshad Number (Easy).
// Specification: https://leetcode.com/problems/harshad-number/description/
// O(d) time, O(1) auxiliary space; d is the decimal digit count of positive x.
function solve(x) {
  let remaining = x;
  let digitSum = 0;
  while (remaining > 0) {
    digitSum += remaining % 10;
    remaining = Math.floor(remaining / 10);
  }
  return x % digitSum === 0 ? digitSum : -1;
}

const sumOfTheDigitsOfHarshadNumber = solve;
class Solution {
  sumOfTheDigitsOfHarshadNumber(x) { return solve(x); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumOfTheDigitsOfHarshadNumber };
