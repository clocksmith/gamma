'use strict';

// 977. Squares of a Sorted Array (Easy).
// Specification: https://leetcode.com/problems/squares-of-a-sorted-array/description/
// O(n) time and space; fill from the largest squared endpoint without sorting.
function solve(nums) {
  const result = new Array(nums.length);
  let left = 0;
  let right = nums.length - 1;
  for (let index = nums.length - 1; index >= 0; index--) {
    if (Math.abs(nums[left]) > Math.abs(nums[right])) {
      result[index] = nums[left] * nums[left];
      left++;
    } else {
      result[index] = nums[right] * nums[right];
      right--;
    }
  }
  return result;
}

const sortedSquares = solve;
class Solution {
  sortedSquares(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sortedSquares };
