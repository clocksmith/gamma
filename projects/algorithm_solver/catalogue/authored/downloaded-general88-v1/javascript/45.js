'use strict';

// 45. Jump Game II (Medium).
// Specification: https://leetcode.com/problems/jump-game-ii/description/
function solve(nums) {
  let jumps = 0; let currentEnd = 0; let farthest = 0;
  for (let i = 0; i < nums.length - 1; i++) {
    farthest = Math.max(farthest, i + nums[i]);
    if (i === currentEnd) { jumps++; currentEnd = farthest; }
  }
  return jumps;
}
const jump = solve;
class Solution { jump(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, jump };
