'use strict';

// 2524. Maximum Frequency Score of a Subarray (Hard).
// Specification: https://leetcode.com/problems/maximum-frequency-score-of-a-subarray/description/
function solve(nums, k) {
  const MOD = 1000000007n;
  function powMod(base, exp) {
    let b = BigInt(base) % MOD; let e = BigInt(exp); let r = 1n;
    while (e > 0n) { if (e & 1n) r = (r * b) % MOD; b = (b * b) % MOD; e >>= 1n; }
    return Number(r);
  }
  const freq = new Map();
  let score = 0;
  const addContrib = (v, f) => { if (f > 0) score = (score + powMod(v, f)) % 1000000007; };
  const subContrib = (v, f) => { if (f > 0) score = (score - powMod(v, f)) % 1000000007; };
  for (let i = 0; i < k; i++) {
    const v = nums[i]; const f = freq.get(v) || 0;
    subContrib(v, f); freq.set(v, f + 1); addContrib(v, f + 1);
  }
  let ans = ((score % 1000000007) + 1000000007) % 1000000007;
  for (let i = k; i < nums.length; i++) {
    const out = nums[i - k]; const inn = nums[i];
    if (out !== inn) {
      let f = freq.get(out);
      subContrib(out, f); freq.set(out, f - 1); addContrib(out, f - 1);
      f = freq.get(inn) || 0;
      subContrib(inn, f); freq.set(inn, f + 1); addContrib(inn, f + 1);
    }
    const cur = ((score % 1000000007) + 1000000007) % 1000000007;
    if (cur > ans) ans = cur;
  }
  return ans;
}
const maxFrequencyScore = solve;
class Solution { maxFrequencyScore(nums, k) { return solve(nums, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxFrequencyScore };
