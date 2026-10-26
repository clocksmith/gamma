'use strict';

// 3026. Maximum Good Subarray Sum: keep the smallest preceding prefix sum for each possible endpoint value.
// O(n) expected time and O(n) auxiliary space; inputs are read-only.
function solve(nums, k) {
  const minimumPrefix = new Map();
  let prefix = 0;
  let best = -Infinity;
  for (const value of nums) {
    prefix += value;
    for (const endpoint of [value - k, value + k]) {
      if (minimumPrefix.has(endpoint)) best = Math.max(best, prefix - minimumPrefix.get(endpoint));
    }
    const before = prefix - value;
    if (!minimumPrefix.has(value) || before < minimumPrefix.get(value)) minimumPrefix.set(value, before);
  }
  return best === -Infinity ? 0 : best;
}

const maximumSubarraySum = solve;
class Solution {
  maximumSubarraySum(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumSubarraySum };
