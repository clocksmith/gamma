'use strict';

// 1742. Maximum Number of Balls in a Box (Easy).
// Specification: https://leetcode.com/problems/maximum-number-of-balls-in-a-box/description/
// O((highLimit - lowLimit + 1) * d) time, O(d) space; d is the digit bound.
function solve(lowLimit, highLimit) {
  const counts = new Map();
  let result = 0;
  for (let value = lowLimit; value <= highLimit; value++) {
    let remaining = value;
    let digitSum = 0;
    while (remaining > 0) {
      digitSum += remaining % 10;
      remaining = Math.floor(remaining / 10);
    }
    const count = (counts.get(digitSum) || 0) + 1;
    counts.set(digitSum, count);
    result = Math.max(result, count);
  }
  return result;
}

const countBalls = solve;
class Solution {
  countBalls(lowLimit, highLimit) { return solve(lowLimit, highLimit); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countBalls };
