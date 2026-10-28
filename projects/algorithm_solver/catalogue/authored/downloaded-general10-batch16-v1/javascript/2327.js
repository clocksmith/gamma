'use strict';

// 2327. Number of People Aware of a Secret (Medium).
// Specification: https://leetcode.com/problems/number-of-people-aware-of-a-secret/description/
function solve(n, delay, forget) {
  const MOD = 1000000007;
  const dp = new Array(n + 1).fill(0);
  dp[1] = 1;
  let window = 0;
  for (let day = 2; day <= n; day++) {
    if (day - delay >= 1) window = (window + dp[day - delay]) % MOD;
    if (day - forget >= 1) window = (window - dp[day - forget] + MOD) % MOD;
    dp[day] = window;
  }
  let ans = 0;
  for (let day = n - forget + 1; day <= n; day++) {
    if (day >= 1) ans = (ans + dp[day]) % MOD;
  }
  return ans;
}
const peopleAwareOfSecret = solve;
class Solution { peopleAwareOfSecret(n, delay, forget) { return solve(n, delay, forget); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, peopleAwareOfSecret };
