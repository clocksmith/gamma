'use strict';

// 3550. Smallest Index With Digit Sum Equal to Index (Easy).
// Specification: https://leetcode.com/problems/smallest-index-with-digit-sum-equal-to-index/description/
// O(n * d) time, O(1) space; d is the maximum digit count; preserve nums.
function solve(nums) {
  for (let index = 0; index < nums.length; index++) {
    let remaining = nums[index];
    let digitSum = 0;
    while (remaining > 0) {
      digitSum += remaining % 10;
      remaining = Math.floor(remaining / 10);
    }
    if (digitSum === index) return index;
  }
  return -1;
}

const smallestIndex = solve;
class Solution {
  smallestIndex(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestIndex };
