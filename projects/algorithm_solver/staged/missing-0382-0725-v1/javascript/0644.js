'use strict';

// 644. Maximum Average Subarray II. Binary search the answer using a minimum-prefix feasibility check for lengths at least k.

function solve(nums, k) {
  function feasible(average) {
    let total = 0;
    for (let i = 0; i < k; i += 1) total += nums[i] - average;
    if (total >= 0) return true;
    let prefix = 0, minimumPrefix = 0;
    for (let i = k; i < nums.length; i += 1) {
      total += nums[i] - average; prefix += nums[i - k] - average;
      minimumPrefix = Math.min(minimumPrefix, prefix);
      if (total - minimumPrefix >= 0) return true;
    }
    return false;
  }
  let low = Infinity, high = -Infinity;
  for (const value of nums) { low = Math.min(low, value); high = Math.max(high, value); }
  for (let iteration = 0; iteration < 60; iteration += 1) {
    const middle = (low + high) / 2;
    if (feasible(middle)) low = middle; else high = middle;
  }
  return low;
}

const findMaxAverage = solve;
class Solution {
  findMaxAverage(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMaxAverage };
