'use strict';

// 553. Optimal Division (Medium).
// Specification: https://leetcode.com/problems/optimal-division/description/
function solve(nums) {
  if (nums.length === 1) return String(nums[0]);
  if (nums.length === 2) return nums[0] + '/' + nums[1];
  return nums[0] + '/(' + nums.slice(1).join('/') + ')';
}
const optimalDivision = solve;
class Solution { optimalDivision(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, optimalDivision };
