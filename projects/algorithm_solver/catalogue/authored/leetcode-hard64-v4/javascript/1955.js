'use strict';

// 1955. Count Number of Special Subsequences. Three stages for nonempty blocks of zeros, ones, and twos; O(n) time and O(1) space. Inputs are preserved.

function solve(nums) {
  const modulus = 1000000007;
  const ways = [0, 0, 0];
  for (const value of nums) {
    const previous = value === 0 ? 1 : ways[value - 1];
    ways[value] = (2 * ways[value] + previous) % modulus;
  }
  return ways[2];
}

const countSpecialSubsequences = solve;
class Solution {
  countSpecialSubsequences(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countSpecialSubsequences };
