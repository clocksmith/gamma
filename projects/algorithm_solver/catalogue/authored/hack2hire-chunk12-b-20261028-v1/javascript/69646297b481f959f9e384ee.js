"use strict";
// Hack2Hire 69646297b481f959f9e384ee (Minimum Coin Combination Counts) over an INFERRED spec; qualification unknown.

function solve(coins, target) {
  const order = coins.map((_, i) => i).sort((a, b) => coins[b] - coins[a]);
  const m = order.length;
  const inf = target + 1;
  const tables = new Array(m + 1);
  tables[m] = new Int32Array(target + 1).fill(inf);
  tables[m][0] = 0;
  for (let pos = m - 1; pos >= 0; pos--) {
    const c = coins[order[pos]];
    const row = Int32Array.from(tables[pos + 1]);
    for (let a = c; a <= target; a++) if (row[a - c] + 1 < row[a]) row[a] = row[a - c] + 1;
    tables[pos] = row;
  }
  if (tables[0][target] >= inf) return [];
  const counts = new Array(coins.length).fill(0);
  let left = target;
  for (let pos = 0; pos < m; pos++) {
    const c = coins[order[pos]];
    const need = tables[pos][left];
    let t = Math.floor(left / c);
    while (tables[pos + 1][left - t * c] !== need - t) t--;
    counts[order[pos]] = t;
    left -= t * c;
  }
  return counts;
}

function minCoinCombination(coins, target) { return solve(coins, target); }

module.exports = solve;
module.exports.minCoinCombination = minCoinCombination;
