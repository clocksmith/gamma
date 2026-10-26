'use strict';

// 2855. Minimum Right Shifts to Sort the Array (Easy).
// Specification: https://leetcode.com/problems/minimum-right-shifts-to-sort-the-array/description/
// O(n) time, O(1) auxiliary space; inputs are distinct and remain unchanged.
function solve(nums) {
  let pivot = -1;
  for (let index = 1; index < nums.length; index++) {
    if (nums[index] < nums[index - 1]) {
      if (pivot !== -1) return -1;
      pivot = index;
    }
  }
  if (pivot === -1) return 0;
  if (nums[nums.length - 1] > nums[0]) return -1;
  return nums.length - pivot;
}

const minimumRightShifts = solve;
class Solution {
  minimumRightShifts(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumRightShifts };
