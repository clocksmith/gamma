'use strict';

// 485. Max Consecutive Ones (Easy).
// Specification: https://leetcode.com/problems/max-consecutive-ones/description/
// O(n) time, O(1) space; preserve nums.
function solve(nums) {
  let current = 0;
  let longest = 0;
  for (const value of nums) {
    current = value === 1 ? current + 1 : 0;
    longest = Math.max(longest, current);
  }
  return longest;
}

const findMaxConsecutiveOnes = solve;
class Solution {
  findMaxConsecutiveOnes(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMaxConsecutiveOnes };
