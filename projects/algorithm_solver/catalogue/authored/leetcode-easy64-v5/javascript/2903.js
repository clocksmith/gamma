'use strict';

// 2903. Find Indices With Index and Value Difference I (Easy).
// Specification: https://leetcode.com/problems/find-indices-with-index-and-value-difference-i/description/
// O(n) time, O(1) auxiliary space; preserve nums; equal indices are allowed when permitted.
function solve(nums, indexDifference, valueDifference) {
  let minimumIndex = 0;
  let maximumIndex = 0;
  for (let right = indexDifference; right < nums.length; right++) {
    const candidate = right - indexDifference;
    if (nums[candidate] < nums[minimumIndex]) minimumIndex = candidate;
    if (nums[candidate] > nums[maximumIndex]) maximumIndex = candidate;
    if (Math.abs(nums[right] - nums[minimumIndex]) >= valueDifference) {
      return [minimumIndex, right];
    }
    if (Math.abs(nums[right] - nums[maximumIndex]) >= valueDifference) {
      return [maximumIndex, right];
    }
  }
  return [-1, -1];
}

const findIndices = solve;
class Solution {
  findIndices(nums, indexDifference, valueDifference) { return solve(nums, indexDifference, valueDifference); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findIndices };
