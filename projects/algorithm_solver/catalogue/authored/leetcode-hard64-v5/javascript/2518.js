'use strict';

// 2518. Number of Great Partitions. Subtract small-sum subsets from all ordered bipartitions; O(n*k) time and O(k) space. Inputs are preserved.

function solve(nums, k) {
  const modulus = 1000000007;
  let sum = 0;
  for (const value of nums) sum += value;
  if (sum < 2 * k) return 0;
  const counts = Array(k).fill(0);
  counts[0] = 1;
  let all = 1;
  for (const value of nums) {
    all = all * 2 % modulus;
    for (let total = k - 1; total >= value; total -= 1) counts[total] = (counts[total] + counts[total - value]) % modulus;
  }
  let invalid = 0;
  for (const count of counts) invalid = (invalid + count) % modulus;
  return ((all - 2 * invalid) % modulus + modulus) % modulus;
}

const countPartitions = solve;
class Solution {
  countPartitions(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPartitions };
