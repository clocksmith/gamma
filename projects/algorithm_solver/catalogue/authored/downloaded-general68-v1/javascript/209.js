'use strict';

// 209. Minimum Size Subarray Sum (Medium).
// Specification: https://leetcode.com/problems/minimum-size-subarray-sum/description/
function solve(target, nums) {
  let left = 0; let total = 0; let shortest = Infinity;
  for (let right = 0; right < nums.length; right++) {
    total += nums[right];
    while (total >= target) { shortest = Math.min(shortest, right - left + 1); total -= nums[left]; left++; }
  }
  return shortest === Infinity ? 0 : shortest;
}
const minSubArrayLen = solve;
class Solution { minSubArrayLen(target, nums) { return solve(target, nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minSubArrayLen };
