"use strict";
// Hack2Hire 69e931b2fbaf3da641828684 (Jump Game Prime) over an INFERRED spec; qualification unknown.

function solve(nums) {
  const n = nums.length;
  const sieve = new Uint8Array(Math.max(n, 2)).fill(1);
  sieve[0] = 0; sieve[1] = 0;
  for (let p = 2; p * p < sieve.length; p++) {
    if (sieve[p]) for (let q = p * p; q < sieve.length; q += p) sieve[q] = 0;
  }
  const strides = [];
  for (let p = 3; p < n; p++) if (sieve[p] && p % 10 === 3) strides.push(p);
  const best = new Array(n).fill(0);
  best[0] = nums[0];
  for (let i = 1; i < n; i++) {
    let top = best[i - 1];
    for (const p of strides) {
      if (p > i) break;
      if (best[i - p] > top) top = best[i - p];
    }
    best[i] = top + nums[i];
  }
  return best[n - 1];
}

function maxJumpScore(nums) { return solve(nums); }

module.exports = solve;
module.exports.maxJumpScore = maxJumpScore;
