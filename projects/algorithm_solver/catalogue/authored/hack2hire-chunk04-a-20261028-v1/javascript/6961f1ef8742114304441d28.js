"use strict";
// Hack2Hire 6961f1ef8742114304441d28 (Target Stock Portfolio Operations) over an INFERRED spec; qualification unknown.

const MOD = 1000000007;

function solve(initial, target, m) {
  const width = Math.max(initial, target) + m + 2;
  let ways = new Array(width).fill(0);
  ways[initial] = 1;
  let total = ways[target];
  for (let step = 1; step <= m; step++) {
    const top = Math.min(initial + step, target + m - step, width - 2);
    const next = new Array(width).fill(0);
    for (let h = 0; h <= top; h++) {
      let value = ways[h + 1];
      if (h) value += ways[h - 1];
      next[h] = value % MOD;
    }
    ways = next;
    total = (total + ways[target]) % MOD;
  }
  return total;
}

function countWays(initial, target, m) { return solve(initial, target, m); }

module.exports = solve;
module.exports.countWays = countWays;
