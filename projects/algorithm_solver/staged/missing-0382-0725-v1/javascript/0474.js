'use strict';

// 474. Ones and Zeroes.

function solve(strs, m, n) {
  const dp = Array.from({length: m + 1}, () => Array(n + 1).fill(0));
  for (const text of strs) {
    let zeros = 0;
    for (const char of text) if (char === '0') zeros += 1;
    const ones = text.length - zeros;
    for (let z = m; z >= zeros; z -= 1) for (let o = n; o >= ones; o -= 1) {
      dp[z][o] = Math.max(dp[z][o], dp[z - zeros][o - ones] + 1);
    }
  }
  return dp[m][n];
}

const findMaxForm = solve;
class Solution {
  findMaxForm(strs, m, n) { return solve(strs, m, n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMaxForm };
