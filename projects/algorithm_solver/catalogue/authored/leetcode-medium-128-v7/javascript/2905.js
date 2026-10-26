'use strict';

// 2905. Find Indices With Index and Value Difference II: track eligible prefix minima and maxima while advancing the right endpoint.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(nums, indexDifference, valueDifference) {
  let smallest = 0;
  let largest = 0;
  for (let right = indexDifference; right < nums.length; right += 1) {
    const entering = right - indexDifference;
    if (nums[entering] < nums[smallest]) smallest = entering;
    if (nums[entering] > nums[largest]) largest = entering;
    if (nums[right] - nums[smallest] >= valueDifference) return [smallest, right];
    if (nums[largest] - nums[right] >= valueDifference) return [largest, right];
  }
  return [-1, -1];
}

const findIndices = solve;
class Solution {
  findIndices(nums, indexDifference, valueDifference) { return solve(nums, indexDifference, valueDifference); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findIndices };
