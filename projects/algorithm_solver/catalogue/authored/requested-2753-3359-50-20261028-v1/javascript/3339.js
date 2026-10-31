"use strict";

const MOD = 1000000007n;

function solve(n, m, k) {
  const even = BigInt(Math.floor(m / 2));
  const odd = BigInt(m) - even;
  let dp0 = new BigInt64Array(k + 1);
  let dp1 = new BigInt64Array(k + 1);
  dp0[0] = even;
  dp1[0] = odd;
  for (let i = 1; i < n; i++) {
    const ndp0 = new BigInt64Array(k + 1);
    const ndp1 = new BigInt64Array(k + 1);
    for (let c = 0; c <= k; c++) {
      const waysAny = (dp0[c] + dp1[c]) % MOD;
      ndp1[c] = (waysAny * odd) % MOD;
      ndp0[c] = (dp1[c] * even) % MOD;
      if (c > 0) ndp0[c] = (ndp0[c] + dp0[c - 1] * even) % MOD;
    }
    dp0 = ndp0;
    dp1 = ndp1;
  }
  return Number((dp0[k] + dp1[k]) % MOD);
}

function countOfArrays(n, m, k) {
  return solve(n, m, k);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.countOfArrays = countOfArrays;
