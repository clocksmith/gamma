'use strict';

// 2547. Minimum Cost to Split an Array. Prefix DP with incremental duplicate penalties for each final segment; O(n^2) time and O(n) space. Inputs are preserved.

function solve(nums, k) {
  const size = nums.length;
  const best = Array(size + 1).fill(Infinity);
  best[0] = 0;
  for (let end = 1; end <= size; end += 1) {
    const counts = new Map();
    let penalty = 0;
    for (let start = end - 1; start >= 0; start -= 1) {
      const value = nums[start];
      const count = (counts.get(value) || 0) + 1;
      counts.set(value, count);
      if (count === 2) penalty += 2;
      else if (count > 2) penalty += 1;
      best[end] = Math.min(best[end], best[start] + k + penalty);
    }
  }
  return best[size];
}

const minCost = solve;
class Solution {
  minCost(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minCost };
