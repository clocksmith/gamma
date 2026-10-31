"use strict";

function totalSum(n) {
  if (n <= 1) return 0n;
  const bn = BigInt(n);
  const iSum = ((bn - 1n) * bn) / 2n;
  let orSum = 0n;
  for (let b = 0; b < 12; b++) {
    const period = 1 << (b + 1);
    const half = 1 << b;
    const full = Math.floor(n / period);
    const rem = n % period;
    const zeros = BigInt(full * half + (rem < half ? rem : half));
    orSum += (bn * bn - zeros * zeros) << BigInt(b);
  }
  return iSum * orSum;
}

function solve(s) {
  const bs = BigInt(s);
  let lo = 1, hi = 1200;
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1;
    if (totalSum(mid) <= bs) lo = mid;
    else hi = mid - 1;
  }
  return lo;
}

function maxSizedArray(s) {
  return solve(s);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.maxSizedArray = maxSizedArray;
