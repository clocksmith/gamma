'use strict';

// 1752. Check if Array Is Sorted and Rotated (Easy).
// Specification: https://leetcode.com/problems/check-if-array-is-sorted-and-rotated/description/
// O(n) time, O(1) space; a circular nondecreasing array has at most one strict drop.
function solve(nums) {
  let drops = 0;
  for (let index = 0; index < nums.length; index++) {
    if (nums[index] > nums[(index + 1) % nums.length]) {
      drops++;
      if (drops > 1) return false;
    }
  }
  return true;
}

const check = solve;
class Solution {
  check(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, check };
