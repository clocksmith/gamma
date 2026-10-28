'use strict';

// 891. Sum of Subsequence Widths (Medium).
// Specification: https://leetcode.com/problems/sum-of-subsequence-widths/description/
function solve(nums) {
  const MOD = 1000000007;
  const sorted = nums.slice().sort((a, b) => a - b);
  const n = sorted.length;
  const pow2 = [1];
  for (let i = 1; i < n; i++) pow2.push(pow2[i - 1] * 2 % MOD);
  let total = 0;
  for (let i = 0; i < n; i++) total = (total + sorted[i] * (pow2[i] - pow2[n - 1 - i])) % MOD;
  return (total + MOD) % MOD;
}
const sumSubseqWidths = solve;
class Solution { sumSubseqWidths(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumSubseqWidths };
