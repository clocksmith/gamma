// Original implementation. Contract: https://leetcode.com/problems/number-of-ways-to-separate-numbers/
"use strict";

function solve(num) {
  const n = num.length;
  const MOD = 1000000007;
  const lcp = Array.from({ length: n + 1 }, () => new Uint16Array(n + 1));
  for (let i = n - 1; i >= 0; i--) {
    for (let j = i + 1; j < n; j++) {
      if (num[i] === num[j]) lcp[i][j] = lcp[i + 1][j + 1] + 1;
    }
  }

  // dp[end][length] counts partitions with final piece length <= length.
  const dp = Array.from({ length: n + 1 }, (_, i) => new Uint32Array(i + 1));
  for (let end = 1; end <= n; end++) {
    for (let length = 1; length <= end; length++) {
      const start = end - length;
      let ways = 0;
      if (num[start] !== "0") {
        if (start === 0) {
          ways = 1;
        } else {
          ways = dp[start][Math.min(start, length - 1)];
          if (length <= start) {
            const previous = start - length;
            const equalPrefix = lcp[previous][start];
            if (equalPrefix >= length || num[previous + equalPrefix] <= num[start + equalPrefix]) {
              ways += dp[start][length] - dp[start][length - 1];
            }
          }
        }
      }
      dp[end][length] = (dp[end][length - 1] + ways + MOD) % MOD;
    }
  }
  return dp[n][n];
}

module.exports = solve;
