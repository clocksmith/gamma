'use strict';

// 1991. Find the Middle Index in Array (Easy).
// Specification: https://leetcode.com/problems/find-the-middle-index-in-array/description/
// O(n) time, O(1) space; return the first index whose excluded left and right sums agree.
function solve(nums) {
  let total = 0;
  for (const value of nums) total += value;
  let left = 0;
  for (let index = 0; index < nums.length; index++) {
    if (left === total - left - nums[index]) return index;
    left += nums[index];
  }
  return -1;
}

const findMiddleIndex = solve;
class Solution {
  findMiddleIndex(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMiddleIndex };
