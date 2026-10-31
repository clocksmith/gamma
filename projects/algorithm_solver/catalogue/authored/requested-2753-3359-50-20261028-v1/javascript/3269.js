"use strict";

function solve(nums1, nums2) {
  const m = nums1.length, n = nums2.length;
  let dp = new Int32Array(n + 1);
  dp[0] = 0;
  for (let j = 1; j <= n; j++) {
    const p = nums2[j - 1];
    const x = dp[j - 1];
    dp[j] = x + 1 + (((x + 1) ^ p) & 1);
  }
  for (let i = 1; i <= m; i++) {
    const p1 = nums1[i - 1];
    const ndp = new Int32Array(n + 1);
    const x0 = dp[0];
    ndp[0] = x0 + 1 + (((x0 + 1) ^ p1) & 1);
    for (let j = 1; j <= n; j++) {
      const p2 = nums2[j - 1];
      const v1 = dp[j] + 1 + (((dp[j] + 1) ^ p1) & 1);
      const v2 = ndp[j - 1] + 1 + (((ndp[j - 1] + 1) ^ p2) & 1);
      ndp[j] = v1 < v2 ? v1 : v2;
    }
    dp = ndp;
  }
  return dp[n];
}

function minLargest(nums1, nums2) {
  return solve(nums1, nums2);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.minLargest = minLargest;
