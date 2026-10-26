'use strict';

// 2448. Minimum Cost to Make Array Equal. Choose a weighted median and sum its absolute deviations; O(n log n) time and O(n) space. Inputs are preserved.

function solve(nums, cost) {
  const ordered = nums.map((value, index) => [value, cost[index]]).sort((a, b) => a[0] - b[0]);
  let totalWeight = 0;
  for (const weight of cost) totalWeight += weight;
  let prefixWeight = 0;
  let median = ordered[0][0];
  for (const [value, weight] of ordered) {
    prefixWeight += weight;
    if (2 * prefixWeight >= totalWeight) { median = value; break; }
  }
  // The stated problem domain bounds the final nonnegative sum by 2^53 - 1.
  let answer = 0;
  for (const [value, weight] of ordered) answer += Math.abs(value - median) * weight;
  return answer;
}

const minCost = solve;
class Solution {
  minCost(nums, cost) { return solve(nums, cost); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minCost };
