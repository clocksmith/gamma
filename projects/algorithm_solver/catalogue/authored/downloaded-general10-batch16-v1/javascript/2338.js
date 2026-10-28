'use strict';

// 2338. Count the Number of Ideal Arrays (Hard).
// Specification: https://leetcode.com/problems/count-the-number-of-ideal-arrays/description/
function solve(n, maxValue) {
  const MOD = 1000000007;
  let prev = new Array(maxValue + 1).fill(1);
  prev[0] = 0;
  for (let len = 2; len <= n; len++) {
    const cur = new Array(maxValue + 1).fill(0);
    for (let d = 1; d <= maxValue; d++) {
      for (let m = d; m <= maxValue; m += d) {
        cur[m] = (cur[m] + prev[d]) % MOD;
      }
    }
    prev = cur;
  }
  let ans = 0;
  for (let v = 1; v <= maxValue; v++) ans = (ans + prev[v]) % MOD;
  return ans;
}
const idealArrays = solve;
class Solution { idealArrays(n, maxValue) { return solve(n, maxValue); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, idealArrays };
