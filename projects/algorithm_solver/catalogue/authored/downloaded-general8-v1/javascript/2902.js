'use strict';

// 2902. Count of Sub-Multisets With Bounded Sum (Hard).
// Specification: https://leetcode.com/problems/count-of-sub-multisets-with-bounded-sum/description/
function solve(nums, l, r) {
  const MOD = 1000000007;
  let zeros = 0;
  const freq = new Map();
  for (const x of nums) {
    if (x === 0) zeros += 1;
    else freq.set(x, (freq.get(x) || 0) + 1);
  }
  let dp = new Array(r + 1).fill(0);
  dp[0] = 1;
  for (const [v, f] of freq) {
    const ndp = new Array(r + 1).fill(0);
    for (let rem = 0; rem < v; rem++) {
      let window = 0;
      for (let s = rem, t = 0; s <= r; s += v, t++) {
        window = (window + dp[s]) % MOD;
        if (t > f) window = (window - dp[s - (f + 1) * v] + MOD) % MOD;
        ndp[s] = window;
      }
    }
    dp = ndp;
  }
  let ans = 0;
  for (let s = l; s <= r; s++) ans = (ans + dp[s]) % MOD;
  return (ans * (zeros + 1)) % MOD;
}
const countSubMultisets = solve;
class Solution {
  countSubMultisets(...args) { return solve(...args); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countSubMultisets };
