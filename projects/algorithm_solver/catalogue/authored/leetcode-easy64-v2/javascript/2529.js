'use strict';

// 2529. Maximum Count of Positive Integer and Negative Integer (Easy).
// Specification: https://leetcode.com/problems/maximum-count-of-positive-integer-and-negative-integer/description/
// O(log n) time, O(1) space; nums is sorted and contains integers.
function solve(nums) {
  function lowerBound(target) {
    let low = 0;
    let high = nums.length;
    while (low < high) {
      const middle = low + Math.floor((high - low) / 2);
      if (nums[middle] < target) low = middle + 1;
      else high = middle;
    }
    return low;
  }
  const negatives = lowerBound(0);
  const positives = nums.length - lowerBound(1);
  return Math.max(negatives, positives);
}

const maximumCount = solve;
class Solution {
  maximumCount(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumCount };
