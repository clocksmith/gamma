// Original candidate implementation. Contract: https://leetcode.com/problems/minimum-total-space-wasted-with-k-resizing-operations/
"use strict";

function solve(nums, k) {
  const n = nums.length;
  const cost = Array.from({ length: n }, () => Array(n).fill(0));
  for (let start = 0; start < n; start++) {
    let maximum = 0;
    let sum = 0;
    for (let end = start; end < n; end++) {
      maximum = Math.max(maximum, nums[end]);
      sum += nums[end];
      cost[start][end] = maximum * (end - start + 1) - sum;
    }
  }
  let dp = Array(n + 1).fill(Infinity);
  dp[0] = 0;
  for (let group = 0; group <= k; group++) {
    const next = Array(n + 1).fill(Infinity);
    next[0] = 0;
    for (let end = 1; end <= n; end++) {
      for (let start = 0; start < end; start++) {
        next[end] = Math.min(next[end], dp[start] + cost[start][end - 1]);
      }
    }
    dp = next;
  }
  return dp[n];
}

module.exports = solve;
