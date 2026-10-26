'use strict';

// 1085. Sum of Digits in the Minimum Number (Easy).
// Specification: https://leetcode.com/problems/sum-of-digits-in-the-minimum-number/description/
// O(n + d) time, O(1) space; return one exactly when the minimum digit sum is even.
function solve(nums) {
  let smallest = nums[0];
  for (const value of nums) smallest = Math.min(smallest, value);
  let digitSum = 0;
  while (smallest > 0) {
    digitSum += smallest % 10;
    smallest = Math.floor(smallest / 10);
  }
  return digitSum % 2 === 0 ? 1 : 0;
}

const sumOfDigits = solve;
class Solution {
  sumOfDigits(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumOfDigits };
