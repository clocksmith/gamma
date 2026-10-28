'use strict';

// 1004. Max Consecutive Ones III (Medium).
// Specification: https://leetcode.com/problems/max-consecutive-ones-iii/description/
function solve(nums, k) {
  let left = 0; let zeros = 0; let best = 0;
  for (let right = 0; right < nums.length; right++) {
    if (nums[right] === 0) zeros++;
    while (zeros > k) { if (nums[left] === 0) zeros--; left++; }
    best = Math.max(best, right - left + 1);
  }
  return best;
}
const longestOnes = solve;
class Solution { longestOnes(nums, k) { return solve(nums, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestOnes };
