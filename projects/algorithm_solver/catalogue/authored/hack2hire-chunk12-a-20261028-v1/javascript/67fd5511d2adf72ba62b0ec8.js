"use strict";
// Hack2Hire 67fd5511d2adf72ba62b0ec8 (Max Fly Distance) over an INFERRED spec; qualification unknown.

function solve(arr, k) {
  if (k === 0) return 0;
  if (k >= arr.length) { let s = 0; for (const a of arr) s += a; return s; }
  let dp = new Array(k + 1).fill(-Infinity), next = new Array(k + 1); // dp[e]: best distance with energy e
  dp[k] = 0;
  for (const a of arr) {
    for (let e = 0; e <= k; e++) {
      const fly = e < k ? dp[e + 1] + a : -Infinity;
      const rest = e === 0 ? -Infinity : e === k ? Math.max(dp[k - 1], dp[k]) : dp[e - 1];
      next[e] = fly > rest ? fly : rest;
    }
    [dp, next] = [next, dp];
  }
  let best = -Infinity;
  for (const d of dp) if (d > best) best = d;
  return best;
}

function maxFlyDistance(arr, k) { return solve(arr, k); }

module.exports = solve;
module.exports.maxFlyDistance = maxFlyDistance;
