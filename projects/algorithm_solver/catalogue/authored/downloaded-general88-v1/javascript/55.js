'use strict';

// 55. Jump Game (Medium).
// Specification: https://leetcode.com/problems/jump-game/description/
function solve(nums) {
  let farthest = 0;
  for (let i = 0; i < nums.length; i++) {
    if (i > farthest) return false;
    farthest = Math.max(farthest, i + nums[i]);
  }
  return true;
}
const canJump = solve;
class Solution { canJump(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, canJump };
