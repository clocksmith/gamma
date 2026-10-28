'use strict';

// 376. Wiggle Subsequence (Medium).
// Specification: https://leetcode.com/problems/wiggle-subsequence/description/
function solve(nums) {
  if (nums.length < 2) return nums.length;
  let up = 1; let down = 1;
  for (let i = 1; i < nums.length; i++) {
    if (nums[i] > nums[i - 1]) up = down + 1;
    else if (nums[i] < nums[i - 1]) down = up + 1;
  }
  return Math.max(up, down);
}
const wiggleMaxLength = solve;
class Solution { wiggleMaxLength(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, wiggleMaxLength };
