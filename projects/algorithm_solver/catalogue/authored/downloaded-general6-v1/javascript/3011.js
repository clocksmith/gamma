'use strict';

// 3011. Find if Array Can Be Sorted (Medium).
// Specification: https://leetcode.com/problems/find-if-array-can-be-sorted/description/
function countBits(x) {
  let count = 0;
  while (x > 0) { count += x & 1; x >>= 1; }
  return count;
}
function solve(nums) {
  let previousMax = -Infinity; let i = 0;
  while (i < nums.length) {
    const bits = countBits(nums[i]);
    let groupMin = nums[i]; let groupMax = nums[i]; let j = i + 1;
    while (j < nums.length && countBits(nums[j]) === bits) {
      groupMin = Math.min(groupMin, nums[j]);
      groupMax = Math.max(groupMax, nums[j]);
      j++;
    }
    if (previousMax > groupMin) return false;
    previousMax = groupMax;
    i = j;
  }
  return true;
}
const canSortArray = solve;
class Solution { canSortArray(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, canSortArray };
