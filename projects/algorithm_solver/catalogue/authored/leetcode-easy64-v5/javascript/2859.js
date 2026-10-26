'use strict';

// 2859. Sum of Values at Indices With K Set Bits (Easy).
// Specification: https://leetcode.com/problems/sum-of-values-at-indices-with-k-set-bits/description/
// O(n log(n + 1)) time, O(1) auxiliary space; indices are at most 999.
function solve(nums, k) {
  let total = 0;
  for (let index = 0; index < nums.length; index++) {
    let remaining = index;
    let bits = 0;
    while (remaining > 0) {
      remaining &= remaining - 1;
      bits++;
    }
    if (bits === k) total += nums[index];
  }
  return total;
}

const sumIndicesWithKSetBits = solve;
class Solution {
  sumIndicesWithKSetBits(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumIndicesWithKSetBits };
