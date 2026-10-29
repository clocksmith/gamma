"use strict";
// Hack2Hire 67803efe6fee41e51af73ddc (Minimum Coins to Form All Amounts) over an INFERRED spec; qualification unknown.

function solve(coins, max) {
  const top = max;
  const kinds = Float64Array.from(new Set(coins)).sort();
  if (kinds[0] !== 1) return -1;
  let reach = 0, count = 0, i = 0;
  const n = kinds.length;
  while (reach < top) {
    while (i < n && kinds[i] <= reach + 1) i++;
    const d = kinds[i - 1];
    let target = top;
    if (i < n && kinds[i] - 1 < target) target = kinds[i] - 1;
    const steps = Math.floor((target - reach + d - 1) / d);
    reach += steps * d;
    count += steps;
  }
  return count;
}

function minCoins(coins, max) { return solve(coins, max); }

module.exports = solve;
module.exports.minCoins = minCoins;
