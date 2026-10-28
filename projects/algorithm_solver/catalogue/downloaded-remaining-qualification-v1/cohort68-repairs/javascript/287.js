'use strict';

// 287. Find the Duplicate Number (Medium).
// Specification: https://leetcode.com/problems/find-the-duplicate-number/description/
function solve(nums) {
  let slow = nums[0], fast = nums[nums[0]];
  while (slow !== fast) { slow = nums[slow]; fast = nums[nums[fast]]; }
  let entry = 0;
  while (entry !== slow) { entry = nums[entry]; slow = nums[slow]; }
  return entry;
}
const findDuplicate = solve;
class Solution { findDuplicate(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findDuplicate };
