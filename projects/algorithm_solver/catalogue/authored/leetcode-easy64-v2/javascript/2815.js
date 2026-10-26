'use strict';

// 2815. Max Pair Sum in an Array (Easy).
// Specification: https://leetcode.com/problems/max-pair-sum-in-an-array/description/
// O(n * d) time, O(1) space; group positive integers by their largest digit.
function solve(nums) {
  const greatest = new Array(10).fill(-1);
  let result = -1;
  for (const value of nums) {
    let remaining = value;
    let largestDigit = 0;
    while (remaining > 0) {
      largestDigit = Math.max(largestDigit, remaining % 10);
      remaining = Math.floor(remaining / 10);
    }
    if (greatest[largestDigit] !== -1) {
      result = Math.max(result, greatest[largestDigit] + value);
    }
    greatest[largestDigit] = Math.max(greatest[largestDigit], value);
  }
  return result;
}

const maxSum = solve;
class Solution {
  maxSum(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSum };
