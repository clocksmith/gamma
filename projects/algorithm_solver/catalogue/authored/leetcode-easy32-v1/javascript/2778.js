'use strict';

// 2778. Sum of Squares of Special Elements (Easy).
// Specification: https://leetcode.com/problems/sum-of-squares-of-special-elements/description/
// O(n) time, O(1) auxiliary space. Divisibility uses one-based positions.
function solve(nums) {
  let result = 0;
  for (let index = 0; index < nums.length; index++) {
    if (nums.length % (index + 1) === 0) result += nums[index] * nums[index];
  }
  return result;
}

const sumOfSquares = solve;
class Solution {
  sumOfSquares(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumOfSquares };
