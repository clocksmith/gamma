'use strict';

// 940. Distinct Subsequences II (Hard).
// Specification: https://leetcode.com/problems/distinct-subsequences-ii/description/
function solve(s) {
  const MOD = 1000000007;
  let total = 1;
  const last = new Array(26).fill(0);
  for (const ch of s) {
    const index = ch.charCodeAt(0) - 97;
    const previous = total;
    total = (2 * total - last[index]) % MOD;
    last[index] = previous;
  }
  return (total - 1 + MOD) % MOD;
}
const distinctSubseqII = solve;
class Solution { distinctSubseqII(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, distinctSubseqII };
