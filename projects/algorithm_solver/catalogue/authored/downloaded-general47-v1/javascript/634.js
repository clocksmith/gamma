'use strict';

// 634. Find the Derangement of Numbers (Medium).
// Specification: https://leetcode.com/problems/find-the-derangement-of-numbers/description/
function solve(n) {
  const MOD = 1000000007;
  if (n === 0) return 1;
  if (n === 1) return 0;
  let previous = 1; let current = 0;
  for (let i = 2; i <= n; i++) {
    const next = ((i - 1) * (previous + current)) % MOD;
    previous = current; current = next;
  }
  return current;
}
const findDerangement = solve;
class Solution { findDerangement(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findDerangement };
