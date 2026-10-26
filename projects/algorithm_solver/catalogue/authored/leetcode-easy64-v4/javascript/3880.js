'use strict';

// 3880. Minimum Absolute Difference Between Two Values (Easy).
// Specification: https://leetcode.com/problems/minimum-absolute-difference-between-two-values/description/
// O(n) time, O(1) space; minimize index distance between a 1 and a 2; preserve nums.
function solve(nums) {
  let lastOne = -1;
  let lastTwo = -1;
  let shortest = nums.length;
  for (let index = 0; index < nums.length; index++) {
    if (nums[index] === 1) {
      lastOne = index;
      if (lastTwo !== -1) shortest = Math.min(shortest, index - lastTwo);
    } else if (nums[index] === 2) {
      lastTwo = index;
      if (lastOne !== -1) shortest = Math.min(shortest, index - lastOne);
    }
  }
  return shortest === nums.length ? -1 : shortest;
}

const minAbsoluteDifference = solve;
class Solution {
  minAbsoluteDifference(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minAbsoluteDifference };
