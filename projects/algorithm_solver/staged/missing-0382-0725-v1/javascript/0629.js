'use strict';

// 629. K Inverse Pairs Array. Sliding-window insertion-count dynamic programming with inversion symmetry.

function solve(n, k) {
  const maximum = n * (n - 1) / 2;
  if (k > maximum) return 0;
  k = Math.min(k, maximum - k);
  const modulus = 1000000007;
  let dp = Array(k + 1).fill(0);
  dp[0] = 1;
  for (let length = 1; length <= n; length += 1) {
    const next = Array(k + 1).fill(0);
    let window = 0;
    for (let inversions = 0; inversions <= k; inversions += 1) {
      window += dp[inversions];
      if (inversions >= length) window -= dp[inversions - length];
      window = (window + modulus) % modulus;
      next[inversions] = window;
    }
    dp = next;
  }
  return dp[k];
}

const kInversePairs = solve;
class Solution {
  kInversePairs(n, k) { return solve(n, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, kInversePairs };
