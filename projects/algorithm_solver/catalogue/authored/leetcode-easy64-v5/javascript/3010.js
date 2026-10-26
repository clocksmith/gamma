'use strict';

// 3010. Divide an Array Into Subarrays With Minimum Cost I (Easy).
// Specification: https://leetcode.com/problems/divide-an-array-into-subarrays-with-minimum-cost-i/description/
// O(n) time, O(1) auxiliary space; choose two smallest starts after index zero.
function solve(nums) {
  let smallest = Infinity;
  let secondSmallest = Infinity;
  for (let index = 1; index < nums.length; index++) {
    const value = nums[index];
    if (value < smallest) {
      secondSmallest = smallest;
      smallest = value;
    } else if (value < secondSmallest) {
      secondSmallest = value;
    }
  }
  return nums[0] + smallest + secondSmallest;
}

const minimumCost = solve;
class Solution {
  minimumCost(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumCost };
