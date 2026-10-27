// Original candidate. Contract: https://leetcode.com/problems/bitwise-or-of-all-subsequence-sums/
"use strict";

function solve(nums) {
  let prefix = 0n;
  let answer = 0n;
  // BigInt preserves bit positions above JavaScript's 32-bit bitwise range.
  for (const x of nums) {
    const value = BigInt(x);
    prefix += value;
    answer |= value | prefix;
  }
  // The contract bounds the result below 2^53, so conversion is exact.
  return Number(answer);
}

module.exports = solve;
