'use strict';

// 2148. Count Elements With Strictly Smaller and Greater Elements (Easy).
// Specification: https://leetcode.com/problems/count-elements-with-strictly-smaller-and-greater-elements/description/
// O(n) time, O(1) space; count values strictly between the extrema; preserve nums.
function solve(nums) {
  let smallest = nums[0];
  let largest = nums[0];
  for (const value of nums) {
    smallest = Math.min(smallest, value);
    largest = Math.max(largest, value);
  }
  let count = 0;
  for (const value of nums) {
    if (value > smallest && value < largest) count++;
  }
  return count;
}

const countElements = solve;
class Solution {
  countElements(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countElements };
