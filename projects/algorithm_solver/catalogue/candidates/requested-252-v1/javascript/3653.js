'use strict';

// 3653. XOR After Range Multiplication Queries I.
// Specification: https://leetcode.com/problems/xor-after-range-multiplication-queries-i/description/
// Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
// O(n + total updated positions) time, O(n) space; modular multiplication is exact.
// Inputs are not modified.

function solve(nums, queries) {
  const values = nums.map(BigInt), modulus = 1000000007n;
  for (const [left, right, step, multiplier] of queries) {
    const factor = BigInt(multiplier);
    for (let index = left; index <= right; index += step) values[index] = values[index] * factor % modulus;
  }
  let answer = 0n;
  for (const value of values) answer ^= value;
  return Number(answer);
}

const xorAfterQueries = solve;
class Solution {
  xorAfterQueries(nums, queries) { return solve(nums, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, xorAfterQueries };
