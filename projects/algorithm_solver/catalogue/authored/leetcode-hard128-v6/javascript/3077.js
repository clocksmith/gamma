'use strict';

// 3077. Maximum Strength of K Disjoint Subarrays.
// Descending-count DP distinguishes an open last interval from completed prefixes; O(n*k) time and O(k) space. Inputs are preserved.

function solve(nums, k) {
  const best = Array(k + 1).fill(-Infinity), ending = Array(k + 1).fill(-Infinity);
  best[0] = 0;
  for (let position = 0; position < nums.length; position += 1) {
    for (let count = Math.min(k, position + 1); count >= 1; count -= 1) {
      const weight = (k - count + 1) * (count % 2 === 1 ? 1 : -1);
      ending[count] = Math.max(ending[count], best[count - 1]) + weight * nums[position];
      best[count] = Math.max(best[count], ending[count]);
    }
  }
  return best[k];
}

const maximumStrength = solve;
class Solution {
  maximumStrength(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumStrength };
