"use strict";
// Hack2Hire 696aacf2cc483345efb1b29f (Minimum Expected Asset Cost) over an INFERRED spec; qualification unknown.

function floorDiv(x, y) {
  const q = x / y;
  return (x % y !== 0n && (x < 0n) !== (y < 0n)) ? q - 1n : q;
}

function solve(n, k, a, b, p) {
  const top = Math.min(k, n);
  const A = BigInt(a), B = BigInt(b), P = BigInt(p);
  const m = B - A + 1n;
  const priceSum = (A + B) * m / 2n;
  let prev = new Array(top + 1).fill(0n);
  let scale = 1n;
  for (let i = 0; i < n; i++) {
    const cur = new Array(top + 1);
    cur[0] = m * prev[0] + scale * priceSum;
    for (let j = 1; j <= top; j++) {
      const keep = prev[j], fixed = P * scale + prev[j - 1];
      let hi = floorDiv(fixed - keep, scale);
      if (hi > B) hi = B;
      if (hi < A) cur[j] = m * fixed;
      else {
        const cnt = hi - A + 1n;
        cur[j] = scale * ((A + hi) * cnt / 2n) + keep * cnt + (m - cnt) * fixed;
      }
    }
    prev = cur;
    scale *= m;
  }
  const million = 1000000n;
  const q = (2n * prev[top] * million + scale) / (2n * scale);
  return (q / million).toString() + "." + (q % million).toString().padStart(6, "0");
}

function minExpectedCost(n, k, a, b, p) { return solve(n, k, a, b, p); }

module.exports = solve;
module.exports.minExpectedCost = minExpectedCost;
