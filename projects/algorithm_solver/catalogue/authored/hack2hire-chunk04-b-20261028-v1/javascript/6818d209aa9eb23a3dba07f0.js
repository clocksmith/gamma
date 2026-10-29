"use strict";
// Hack2Hire 6818d209aa9eb23a3dba07f0 (Color a Row of Houses) over an INFERRED spec; qualification unknown.

const MOD = 1000000007n;

function power(base, exponent) {
  let result = 1n;
  base %= MOD;
  while (exponent > 0n) {
    if (exponent & 1n) result = (result * base) % MOD;
    base = (base * base) % MOD;
    exponent >>= 1n;
  }
  return result;
}

function solve(n, k, firstHouseColor, lastHouseColor) {
  const N = BigInt(n), K = BigInt(k);
  const p = power(K - 1n, N - 1n);
  const sign = (N - 1n) % 2n === 0n ? 1n : MOD - 1n;
  const numerator = firstHouseColor === lastHouseColor ? (p + (K - 1n) * sign) % MOD : (p - sign + MOD) % MOD;
  return Number((numerator * power(K, MOD - 2n)) % MOD);
}

function countWays(n, k, firstHouseColor, lastHouseColor) { return solve(n, k, firstHouseColor, lastHouseColor); }

module.exports = solve;
module.exports.countWays = countWays;
