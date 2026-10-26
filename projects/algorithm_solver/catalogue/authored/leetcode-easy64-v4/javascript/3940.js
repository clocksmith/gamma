'use strict';

// 3940. Limit Occurrences in Sorted Array (Easy).
// Specification: https://leetcode.com/problems/limit-occurrences-in-sorted-array/description/
// O(n) time, O(1) auxiliary space beyond the output; return a new array and preserve nums.
function solve(nums, k) {
  const result = [];
  for (const value of nums) {
    if (result.length < k || value !== result[result.length - k]) result.push(value);
  }
  return result;
}

const limitOccurrences = solve;
class Solution {
  limitOccurrences(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, limitOccurrences };
