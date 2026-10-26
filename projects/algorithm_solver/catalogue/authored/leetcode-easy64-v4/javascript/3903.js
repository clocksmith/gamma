'use strict';

// 3903. Smallest Stable Index I (Easy).
// Specification: https://leetcode.com/problems/smallest-stable-index-i/description/
// O(n) time and space; both prefix maximum and suffix minimum include the candidate index.
function solve(nums, k) {
  const suffixMinimum = new Array(nums.length);
  suffixMinimum[nums.length - 1] = nums[nums.length - 1];
  for (let index = nums.length - 2; index >= 0; index--) {
    suffixMinimum[index] = Math.min(nums[index], suffixMinimum[index + 1]);
  }
  let prefixMaximum = nums[0];
  for (let index = 0; index < nums.length; index++) {
    prefixMaximum = Math.max(prefixMaximum, nums[index]);
    if (prefixMaximum - suffixMinimum[index] <= k) return index;
  }
  return -1;
}

const firstStableIndex = solve;
class Solution {
  firstStableIndex(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, firstStableIndex };
