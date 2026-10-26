'use strict';

// 3686. Number of Stable Subsequences.
// O(n) time and O(1) auxiliary space; count nonempty subsequences modulo 1e9+7.
function solve(nums) {
  const modulus = 1000000007;
  const single = [0, 0];
  const double = [0, 0];
  for (const value of nums) {
    const parity = value % 2;
    const opposite = 1 - parity;
    const addedSingle = (1 + single[opposite] + double[opposite]) % modulus;
    const addedDouble = single[parity];
    single[parity] = (single[parity] + addedSingle) % modulus;
    double[parity] = (double[parity] + addedDouble) % modulus;
  }
  return (single[0] + single[1] + double[0] + double[1]) % modulus;
}

const countStableSubsequences = solve;
class Solution {
  countStableSubsequences(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countStableSubsequences };
