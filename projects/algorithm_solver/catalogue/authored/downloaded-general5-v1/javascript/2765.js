'use strict';

// 2765. Longest Alternating Subarray (Easy).
// Specification: https://leetcode.com/problems/longest-alternating-subarray/description/
function solve(nums) {
  let best = -1;
  for (let i = 0; i < nums.length; i++) {
    let expected = 1; let j = i;
    while (j + 1 < nums.length && nums[j + 1] - nums[j] === expected) {
      j++; expected *= -1;
    }
    if (j - i + 1 > 1) best = Math.max(best, j - i + 1);
  }
  return best;
}
const alternatingSubarray = solve;
class Solution { alternatingSubarray(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, alternatingSubarray };
