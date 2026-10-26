'use strict';

// 3500. Minimum Cost to Divide Array Into Subarrays.
// Charge each segment start for all later cost weights, eliminating the segment-count state; O(n^2) time and O(n) space. Inputs are preserved.

function solve(nums, cost, k) {
  const n = nums.length, values = [0], weights = [0], best = Array(n + 1).fill(0);
  for (let index = 0; index < n; index += 1) {
    values.push(values[index] + nums[index]); weights.push(weights[index] + cost[index]);
  }
  for (let start = n - 1; start >= 0; start -= 1) {
    const surcharge = k * (weights[n] - weights[start]);
    best[start] = Infinity;
    for (let end = start + 1; end <= n; end += 1) best[start] = Math.min(best[start], values[end] * (weights[end] - weights[start]) + surcharge + best[end]);
  }
  return best[0];
}

const minimumCost = solve;
class Solution {
  minimumCost(nums, cost, k) { return solve(nums, cost, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumCost };
