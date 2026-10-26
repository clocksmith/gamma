'use strict';

// 3818. Minimum Prefix Removal to Make Array Strictly Increasing.
// O(n) time and O(1) space; locate the longest strictly increasing suffix.
function solve(nums) {
  let left = nums.length - 1;
  while (left > 0 && nums[left - 1] < nums[left]) left -= 1;
  return left;
}

const minimumPrefixLength = solve;
class Solution {
  minimumPrefixLength(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumPrefixLength };
