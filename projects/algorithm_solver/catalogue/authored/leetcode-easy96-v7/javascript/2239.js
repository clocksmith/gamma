'use strict';

// 2239. Find Closest Number to Zero (Easy).
// Specification: https://leetcode.com/problems/find-closest-number-to-zero/description/
// O(n) time, O(1) space; prefer the larger value on equal absolute distance; preserve nums.
function solve(nums) {
  let best = nums[0];
  for (const value of nums) {
    if (Math.abs(value) < Math.abs(best) ||
        (Math.abs(value) === Math.abs(best) && value > best)) {
      best = value;
    }
  }
  return best;
}

const findClosestNumber = solve;
class Solution {
  findClosestNumber(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findClosestNumber };
