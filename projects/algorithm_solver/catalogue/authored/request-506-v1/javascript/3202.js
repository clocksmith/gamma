// Original candidate implementation. Contract: https://leetcode.com/problems/find-the-maximum-length-of-valid-subsequence-ii/
"use strict";

function solve(nums, k) {
  const dp = Array.from({ length: k }, () => new Int32Array(k));
  let answer = 0;
  for (const value of nums) {
    const remainder = value % k;
    for (let previous = 0; previous < k; previous++) {
      dp[remainder][previous] = dp[previous][remainder] + 1;
      answer = Math.max(answer, dp[remainder][previous]);
    }
  }
  return answer;
}

module.exports = solve;
