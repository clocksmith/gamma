'use strict';

// 164. Maximum Gap (Medium).
// Specification: https://leetcode.com/problems/maximum-gap/description/
function solve(nums) {
  if (nums.length < 2) return 0;
  const sorted = nums.slice().sort((a, b) => a - b);
  let best = 0;
  for (let i = 1; i < sorted.length; i++) best = Math.max(best, sorted[i] - sorted[i - 1]);
  return best;
}
const maximumGap = solve;
class Solution { maximumGap(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumGap };
