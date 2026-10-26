'use strict';

// 2911. Minimum Changes to Make K Semi-palindromes.
// Precompute every proper-divisor palindrome cost, then partition prefixes; O(n^3 log n + k*n^2) time, O(n^2) space.

function solve(s, k) {
  const n = s.length, divisors = Array.from({ length: n + 1 }, () => []);
  for (let step = 1; 2 * step <= n; step += 1) for (let length = 2 * step; length <= n; length += step) divisors[length].push(step);
  const cost = Array.from({ length: n }, () => Array(n).fill(n));
  for (let start = 0; start < n; start += 1) {
    for (let length = 2; start + length <= n; length += 1) {
      for (const step of divisors[length]) {
        let edits = 0;
        for (let offset = 0; offset < step; offset += 1) {
          for (let left = start + offset, right = start + length - step + offset; left < right; left += step, right -= step) edits += Number(s[left] !== s[right]);
        }
        cost[start][start + length - 1] = Math.min(cost[start][start + length - 1], edits);
      }
    }
  }
  let dp = Array(n + 1).fill(n); dp[0] = 0;
  for (let parts = 1; parts <= k; parts += 1) {
    const following = Array(n + 1).fill(n);
    for (let end = 2 * parts; end <= n; end += 1) {
      for (let start = 2 * (parts - 1); start <= end - 2; start += 1) following[end] = Math.min(following[end], dp[start] + cost[start][end - 1]);
    }
    dp = following;
  }
  return dp[n];
}

const minimumChanges = solve;
class Solution {
  minimumChanges(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumChanges };
