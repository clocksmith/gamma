'use strict';

// 3300. Minimum Element After Replacement With Digit Sum (Easy).
// Specification: https://leetcode.com/problems/minimum-element-after-replacement-with-digit-sum/description/
// O(n log M) time, O(1) space; compute replacement values without changing nums.
function solve(nums) {
  let smallest = Infinity;
  for (const value of nums) {
    let remaining = value;
    let digitSum = 0;
    while (remaining > 0) {
      digitSum += remaining % 10;
      remaining = Math.floor(remaining / 10);
    }
    smallest = Math.min(smallest, digitSum);
  }
  return smallest;
}

const minElement = solve;
class Solution {
  minElement(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minElement };
