'use strict';

// 1498. Number of Subsequences That Satisfy the Given Sum Condition (Medium).
// Specification: https://leetcode.com/problems/number-of-subsequences-that-satisfy-the-given-sum-condition/description/
function solve(nums, target) {
  const MOD = 1000000007;
  const sorted = nums.slice().sort((a, b) => a - b);
  const powers = new Array(sorted.length + 1).fill(1);
  for (let i = 1; i <= sorted.length; i++) powers[i] = (powers[i - 1] * 2) % MOD;
  let left = 0; let right = sorted.length - 1; let count = 0;
  while (left <= right) {
    if (sorted[left] + sorted[right] <= target) { count = (count + powers[right - left]) % MOD; left++; }
    else right--;
  }
  return count;
}
const numSubseq = solve;
class Solution { numSubseq(nums, target) { return solve(nums, target); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numSubseq };
