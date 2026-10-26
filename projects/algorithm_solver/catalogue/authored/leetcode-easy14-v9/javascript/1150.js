'use strict';

// 1150. Check If a Number Is Majority Element in a Sorted Array (Easy).
// Specification: https://leetcode.com/problems/check-if-a-number-is-majority-element-in-a-sorted-array/description/
// O(log n) time, O(1) space; locate the first target and check its strict-majority endpoint.
function solve(nums, target) {
  let left = 0;
  let right = nums.length;
  while (left < right) {
    const middle = left + Math.floor((right - left) / 2);
    if (nums[middle] < target) {
      left = middle + 1;
    } else {
      right = middle;
    }
  }
  const lastRequired = left + Math.floor(nums.length / 2);
  return lastRequired < nums.length && nums[lastRequired] === target;
}

const isMajorityElement = solve;
class Solution {
  isMajorityElement(nums, target) { return solve(nums, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isMajorityElement };
