"use strict";

const MOD = 1000000007;

function solve(s) {
  let dp = [1];
  for (let idx = 0; idx < s.length; idx++) {
    if (s[idx] === "I") {
      let cur = 0;
      const ndp = new Array(dp.length + 1);
      for (let i = 0; i < dp.length; i++) {
        cur = (cur + dp[i]) % MOD;
        ndp[i] = cur;
      }
      ndp.pop();
      dp = ndp;
    } else {
      let cur = 0;
      const ndp = new Array(dp.length + 1).fill(0);
      for (let i = dp.length - 1; i >= 0; i--) {
        cur = (cur + dp[i]) % MOD;
        ndp[i] = cur;
      }
      dp = ndp;
    }
  }
  let ans = 0;
  for (let i = 0; i < dp.length; i++) ans = (ans + dp[i]) % MOD;
  return ans;
}

function numPermsDISequence(s) {
  return solve(s);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.numPermsDISequence = numPermsDISequence;
