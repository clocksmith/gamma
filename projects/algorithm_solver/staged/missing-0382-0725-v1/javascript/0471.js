'use strict';

// 471. Encode String with Shortest Length. Interval dynamic programming considers splits and repeated encoded units; ties keep an existing optimum.

function solve(s) {
  const n = s.length;
  if (n === 0) return '';
  const dp = Array.from({length: n}, () => Array(n).fill(''));
  for (let length = 1; length <= n; length += 1) {
    for (let left = 0; left + length <= n; left += 1) {
      const right = left + length - 1, text = s.slice(left, right + 1);
      let best = text;
      for (let split = left; split < right; split += 1) {
        const candidate = dp[left][split] + dp[split + 1][right];
        if (candidate.length < best.length) best = candidate;
      }
      for (let period = 1; period <= Math.floor(length / 2); period += 1) {
        if (length % period === 0 && text === text.slice(0, period).repeat(length / period)) {
          const candidate = String(length / period) + '[' + dp[left][left + period - 1] + ']';
          if (candidate.length < best.length) best = candidate;
        }
      }
      dp[left][right] = best;
    }
  }
  return dp[0][n - 1];
}

const encode = solve;
class Solution {
  encode(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, encode };
