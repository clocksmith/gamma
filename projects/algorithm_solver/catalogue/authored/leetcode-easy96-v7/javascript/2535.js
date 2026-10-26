'use strict';

// 2535. Difference Between Element Sum and Digit Sum of an Array (Easy).
// Specification: https://leetcode.com/problems/difference-between-element-sum-and-digit-sum-of-an-array/description/
// O(n * d) time, O(1) space for at most d digits per value; preserve nums.
function solve(nums) {
  let elementSum = 0;
  let digitSum = 0;
  for (const value of nums) {
    elementSum += value;
    let remaining = value;
    while (remaining > 0) {
      digitSum += remaining % 10;
      remaining = Math.floor(remaining / 10);
    }
  }
  return Math.abs(elementSum - digitSum);
}

const differenceOfSum = solve;
class Solution {
  differenceOfSum(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, differenceOfSum };
