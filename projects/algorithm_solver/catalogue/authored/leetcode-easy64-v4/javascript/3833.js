'use strict';

// 3833. Count Dominant Indices (Easy).
// Specification: https://leetcode.com/problems/count-dominant-indices/description/
// O(n) time, O(1) space; compare averages by exact cross multiplication; preserve nums.
function solve(nums) {
  let suffixSum = nums[nums.length - 1];
  let suffixCount = 1;
  let result = 0;
  for (let index = nums.length - 2; index >= 0; index--) {
    if (nums[index] * suffixCount > suffixSum) result++;
    suffixSum += nums[index];
    suffixCount++;
  }
  return result;
}

const dominantIndices = solve;
class Solution {
  dominantIndices(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, dominantIndices };
