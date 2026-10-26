'use strict';

// 704. Binary Search (Easy).
// Specification: https://leetcode.com/problems/binary-search/description/
// O(log n) time, O(1) space; narrow an inclusive sorted interval.
function solve(nums, target) {
  let left = 0;
  let right = nums.length - 1;
  while (left <= right) {
    const middle = left + Math.floor((right - left) / 2);
    if (nums[middle] === target) return middle;
    if (nums[middle] < target) left = middle + 1;
    else right = middle - 1;
  }
  return -1;
}

const search = solve;
class Solution {
  search(nums, target) { return solve(nums, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, search };
