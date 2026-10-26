'use strict';

// 2176. Count Equal and Divisible Pairs in an Array (Easy).
// Specification: https://leetcode.com/problems/count-equal-and-divisible-pairs-in-an-array/description/
// O(n^2) time, O(1) space; divisibility applies to indices, not values.
function solve(nums, k) {
  let result = 0;
  for (let left = 0; left < nums.length; left++) {
    for (let right = left + 1; right < nums.length; right++) {
      if (nums[left] === nums[right] && left * right % k === 0) result++;
    }
  }
  return result;
}

const countPairs = solve;
class Solution {
  countPairs(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPairs };
