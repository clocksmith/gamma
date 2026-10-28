'use strict';

// 2344. Minimum Deletions to Make Array Divisible (Medium).
// Specification: https://leetcode.com/problems/minimum-deletions-to-make-array-divisible/description/
function solve(nums, numsDivide) {
  const gcd = (a, b) => (b === 0 ? a : gcd(b, a % b));
  let g = numsDivide[0];
  for (const v of numsDivide) g = gcd(g, v);
  const sorted = nums.slice().sort((a, b) => a - b);
  for (let i = 0; i < sorted.length; i++) {
    if (g % sorted[i] === 0) return i;
  }
  return -1;
}
const minOperations = solve;
class Solution { minOperations(nums, numsDivide) { return solve(nums, numsDivide); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
