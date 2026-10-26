'use strict';

// 2057. Smallest Index With Equal Value (Easy).
// Specification: https://leetcode.com/problems/smallest-index-with-equal-value/description/
// O(n) time, O(1) space; return the first matching index; preserve nums.
function solve(nums) {
  for (let index = 0; index < nums.length; index++) {
    if (index % 10 === nums[index]) return index;
  }
  return -1;
}

const smallestEqual = solve;
class Solution {
  smallestEqual(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestEqual };
