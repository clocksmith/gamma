'use strict';

// 2539. Count the Number of Good Subsequences (Medium).
// Specification: https://leetcode.com/problems/count-the-number-of-good-subsequences/description/
function solve(s) {
  const MOD = 1000000007n;
  const freq = new Map();
  for (const ch of s) freq.set(ch, (freq.get(ch) || 0) + 1);
  const counts = Array.from(freq.values());
  const mx = Math.max(...counts);
  const fact = [1n]; const invFact = [1n];
  for (let i = 1; i <= mx; i++) fact[i] = (fact[i - 1] * BigInt(i)) % MOD;
  function modPow(b, e) { let r = 1n; let x = b % MOD; while (e > 0n) { if (e & 1n) r = (r * x) % MOD; x = (x * x) % MOD; e >>= 1n; } return r; }
  invFact[mx] = modPow(fact[mx], MOD - 2n);
  for (let i = mx; i > 0; i--) invFact[i - 1] = (invFact[i] * BigInt(i)) % MOD;
  function comb(n, k) {
    if (k < 0 || k > n) return 0n;
    return (((fact[n] * invFact[k]) % MOD) * invFact[n - k]) % MOD;
  }
  let ans = 0n;
  for (let f = 1; f <= mx; f++) {
    let prod = 1n;
    for (const c of counts) prod = (prod * (comb(c, f) + 1n)) % MOD;
    ans = (ans + prod - 1n) % MOD;
  }
  return Number((ans + MOD) % MOD);
}
const countGoodSubsequences = solve;
class Solution { countGoodSubsequences(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, countGoodSubsequences };
