'use strict';

// 3082. Find the Sum of the Power of All Subsequences.
// Weighted subset DP counts unused elements in two ways; O(n*k) time and O(k) space. Inputs are preserved.

function solve(nums, k) {
  const modulus = 1000000007;
  let ways = Array(k + 1).fill(0); ways[0] = 1;
  for (const value of nums) {
    const following = ways.map(count => 2 * count % modulus);
    for (let total = value; total <= k; total += 1) following[total] = (following[total] + ways[total - value]) % modulus;
    ways = following;
  }
  return ways[k];
}

const sumOfPower = solve;
class Solution {
  sumOfPower(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumOfPower };
