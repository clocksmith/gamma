'use strict';

// 915. Partition Array into Disjoint Intervals (Medium).
// Specification: https://leetcode.com/problems/partition-array-into-disjoint-intervals/description/
function solve(nums) {
  const n = nums.length;
  const rightMin = new Array(n);
  rightMin[n - 1] = nums[n - 1];
  for (let i = n - 2; i >= 0; i--) rightMin[i] = Math.min(nums[i], rightMin[i + 1]);
  let leftMax = nums[0];
  for (let i = 0; i < n - 1; i++) {
    leftMax = Math.max(leftMax, nums[i]);
    if (leftMax <= rightMin[i + 1]) return i + 1;
  }
  return n;
}
const partitionDisjoint = solve;
class Solution { partitionDisjoint(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, partitionDisjoint };
