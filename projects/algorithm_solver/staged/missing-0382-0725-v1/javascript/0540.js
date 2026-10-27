'use strict';

// 540. Single Element in a Sorted Array.

function solve(nums) {
  let left = 0, right = nums.length - 1;
  while (left < right) {
    let middle = Math.floor((left + right) / 2);
    middle -= middle % 2;
    if (nums[middle] === nums[middle + 1]) left = middle + 2;
    else right = middle;
  }
  return nums[left];
}

const singleNonDuplicate = solve;
class Solution {
  singleNonDuplicate(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, singleNonDuplicate };
