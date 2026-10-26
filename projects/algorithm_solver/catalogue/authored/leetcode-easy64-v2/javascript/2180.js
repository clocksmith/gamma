'use strict';

// 2180. Count Integers With Even Digit Sum (Easy).
// Specification: https://leetcode.com/problems/count-integers-with-even-digit-sum/description/
// O(num * d) time, O(1) space; d is the digit count of num.
function solve(num) {
  let result = 0;
  for (let value = 1; value <= num; value++) {
    let remaining = value;
    let digitSum = 0;
    while (remaining > 0) {
      digitSum += remaining % 10;
      remaining = Math.floor(remaining / 10);
    }
    if (digitSum % 2 === 0) result++;
  }
  return result;
}

const countEven = solve;
class Solution {
  countEven(num) { return solve(num); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countEven };
