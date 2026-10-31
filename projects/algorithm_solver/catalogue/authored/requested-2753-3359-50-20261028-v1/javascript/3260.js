"use strict";

function solve(n, k) {
  const m = (n + 1) >> 1;
  const pow10 = new Int32Array(n);
  pow10[0] = 1 % k;
  for (let i = 1; i < n; i++) pow10[i] = (pow10[i - 1] * 10) % k;
  const weights = new Int32Array(m);
  for (let i = 0; i < m; i++) {
    const j = n - 1 - i;
    weights[i] = i === j ? pow10[i] : (pow10[i] + pow10[j]) % k;
  }
  const dp = new Uint8Array((m + 1) * k);
  dp[m * k + 0] = 1;
  for (let i = m - 1; i >= 0; i--) {
    const w = weights[i];
    const lo = i === 0 ? 1 : 0;
    for (let r = 0; r < k; r++) {
      for (let d = 9; d >= lo; d--) {
        if (dp[(i + 1) * k + ((r + d * w) % k)]) {
          dp[i * k + r] = 1;
          break;
        }
      }
    }
  }
  const left = new Array(m);
  let r = 0;
  for (let i = 0; i < m; i++) {
    const w = weights[i];
    const lo = i === 0 ? 1 : 0;
    for (let d = 9; d >= lo; d--) {
      if (dp[(i + 1) * k + ((r + d * w) % k)]) {
        left[i] = String(d);
        r = (r + d * w) % k;
        break;
      }
    }
  }
  const half = n >> 1;
  const right = new Array(half);
  for (let i = 0; i < half; i++) right[i] = left[half - 1 - i];
  return left.join("") + right.join("");
}

function largestPalindrome(n, k) {
  return solve(n, k);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.largestPalindrome = largestPalindrome;
