'use strict';

// 3925. Concatenate Array With Reverse (Easy).
// Specification: https://leetcode.com/problems/concatenate-array-with-reverse/description/
// O(n) time and output space; do not mutate or return the input array.
function solve(nums) {
  const result = nums.slice();
  for (let index = nums.length - 1; index >= 0; index--) result.push(nums[index]);
  return result;
}

const concatWithReverse = solve;
class Solution {
  concatWithReverse(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, concatWithReverse };
