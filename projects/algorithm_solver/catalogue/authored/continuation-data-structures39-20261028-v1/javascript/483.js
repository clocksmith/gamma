"use strict";

function solve(n) {
  const N = BigInt(n);
  let maxM = 0;
  for (let tmp = N; tmp > 0n; tmp >>= 1n) maxM++;
  for (let m = maxM; m >= 2; m--) {
    let low = 2n;
    let high = BigInt(Math.floor(Math.pow(Number(N), 1.0 / m))) + 2n;
    if (high >= N) high = N - 1n;
    if (low > high) low = 2n;
    while (low <= high) {
      const mid = (low + high) >> 1n;
      let total = 1n;
      let cur = 1n;
      for (let i = 0; i < m; i++) {
        cur *= mid;
        total += cur;
        if (total > N) break;
      }
      if (total === N) return mid.toString();
      if (total < N) low = mid + 1n;
      else high = mid - 1n;
    }
  }
  return (N - 1n).toString();
}

function smallestGoodBase(n) {
  return solve(n);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.smallestGoodBase = smallestGoodBase;
