'use strict';

// 2016. Maximum Difference Between Increasing Elements (Easy).
// Specification: https://leetcode.com/problems/maximum-difference-between-increasing-elements/description/
// O(n) time, O(1) space; require a strictly larger later value; preserve nums.
function solve(nums) {
  let smallest = nums[0];
  let greatestDifference = -1;
  for (let index = 1; index < nums.length; index++) {
    if (nums[index] > smallest) {
      greatestDifference = Math.max(greatestDifference, nums[index] - smallest);
    }
    smallest = Math.min(smallest, nums[index]);
  }
  return greatestDifference;
}

const maximumDifference = solve;
class Solution {
  maximumDifference(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumDifference };
