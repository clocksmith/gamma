'use strict';

// 34. Find First and Last Position of Element in Sorted Array (Medium).
// Specification: https://leetcode.com/problems/find-first-and-last-position-of-element-in-sorted-array/description/
function bound(nums, target, first) {
  let left = 0; let right = nums.length - 1; let answer = -1;
  while (left <= right) {
    const mid = Math.floor((left + right) / 2);
    if (nums[mid] === target) { answer = mid; if (first) right = mid - 1; else left = mid + 1; }
    else if (nums[mid] < target) left = mid + 1;
    else right = mid - 1;
  }
  return answer;
}
function solve(nums, target) { return [bound(nums, target, true), bound(nums, target, false)]; }
const searchRange = solve;
class Solution { searchRange(nums, target) { return solve(nums, target); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, searchRange };
