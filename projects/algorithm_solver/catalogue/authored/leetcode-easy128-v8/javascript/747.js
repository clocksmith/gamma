'use strict';

// 747. Largest Number At Least Twice of Others (Easy).
// Specification: https://leetcode.com/problems/largest-number-at-least-twice-of-others/description/
// O(n) time, O(1) space; keep the largest and second-largest nonnegative values.
function solve(nums) {
  let largest = -1;
  let second = -1;
  let answer = -1;
  for (let index = 0; index < nums.length; index++) {
    const value = nums[index];
    if (value > largest) {
      second = largest;
      largest = value;
      answer = index;
    } else {
      second = Math.max(second, value);
    }
  }
  return largest >= 2 * second ? answer : -1;
}

const dominantIndex = solve;
class Solution {
  dominantIndex(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, dominantIndex };
