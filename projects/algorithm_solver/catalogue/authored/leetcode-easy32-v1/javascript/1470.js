'use strict';

// 1470. Shuffle the Array (Easy).
// Specification: https://leetcode.com/problems/shuffle-the-array/description/
// O(n) time, O(1) auxiliary space excluding the fresh output. Preserve nums.
function solve(nums, n) {
  const result = [];
  for (let index = 0; index < n; index++) {
    result.push(nums[index], nums[index + n]);
  }
  return result;
}

const shuffle = solve;
class Solution {
  shuffle(nums, n) { return solve(nums, n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, shuffle };
