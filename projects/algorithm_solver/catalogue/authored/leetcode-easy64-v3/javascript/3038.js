'use strict';

// 3038. Maximum Number of Operations With the Same Score I (Easy).
// Specification: https://leetcode.com/problems/maximum-number-of-operations-with-the-same-score-i/description/
// O(n) time, O(1) space; inspect consecutive disjoint pairs without deleting inputs.
function solve(nums) {
  const score = nums[0] + nums[1];
  let operations = 0;
  for (let index = 0; index + 1 < nums.length; index += 2) {
    if (nums[index] + nums[index + 1] !== score) break;
    operations++;
  }
  return operations;
}

const maxOperations = solve;
class Solution {
  maxOperations(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxOperations };
