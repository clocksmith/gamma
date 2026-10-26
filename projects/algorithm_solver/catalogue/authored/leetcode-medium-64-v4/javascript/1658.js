'use strict';

// 1658. Minimum Operations to Reduce X to Zero: keep the longest positive-value subarray whose sum is total minus x.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(nums, x) {
  let target = -x;
  for (const value of nums) target += value;
  if (target < 0) return -1;
  if (target === 0) return nums.length;
  let left = 0;
  let total = 0;
  let longest = -1;
  for (let right = 0; right < nums.length; right += 1) {
    total += nums[right];
    while (total > target) {
      total -= nums[left];
      left += 1;
    }
    if (total === target) longest = Math.max(longest, right - left + 1);
  }
  return longest >= 0 ? nums.length - longest : -1;
}

const minOperations = solve;
class Solution {
  minOperations(nums, x) { return solve(nums, x); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
