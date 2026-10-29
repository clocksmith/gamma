"use strict";

function solve(n, k) {
  if (n === 1) return k;
  let same = k;
  let diff = k * (k - 1);
  for (let i = 3; i <= n; i++) {
    const nextDiff = (same + diff) * (k - 1);
    same = diff;
    diff = nextDiff;
  }
  return same + diff;
}

function numWays(n, k) {
  return solve(n, k);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.numWays = numWays;
