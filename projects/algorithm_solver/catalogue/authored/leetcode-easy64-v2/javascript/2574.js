'use strict';

// 2574. Left and Right Sum Differences (Easy).
// Specification: https://leetcode.com/problems/left-and-right-sum-differences/description/
// O(n) time, O(n) output space; preserve nums.
function solve(nums) {
  let right = 0;
  for (const value of nums) right += value;
  let left = 0;
  const result = [];
  for (const value of nums) {
    right -= value;
    result.push(Math.abs(left - right));
    left += value;
  }
  return result;
}

const leftRightDifference = solve;
class Solution {
  leftRightDifference(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, leftRightDifference };
