'use strict';

// 3689. Maximum Total Subarray Value I.
// O(n) time and O(1) auxiliary space; repeated selection of the full interval is allowed.
function solve(nums, k) {
  let smallest = nums[0];
  let largest = nums[0];
  for (const value of nums) {
    smallest = Math.min(smallest, value);
    largest = Math.max(largest, value);
  }
  return (largest - smallest) * k;
}

const maxTotalValue = solve;
class Solution {
  maxTotalValue(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxTotalValue };
