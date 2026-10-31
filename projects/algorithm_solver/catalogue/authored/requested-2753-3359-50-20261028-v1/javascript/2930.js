"use strict";

const MOD = 1000000007n;

function modPow(base, exp) {
  let res = 1n;
  let b = BigInt(base) % MOD;
  let e = BigInt(exp);
  while (e > 0n) {
    if (e & 1n) res = (res * b) % MOD;
    b = (b * b) % MOD;
    e >>= 1n;
  }
  return res;
}

function solve(n) {
  if (n < 4) return 0;
  const bn = BigInt(n);
  const p26 = modPow(26n, bn);
  const p25 = (modPow(25n, bn - 1n) * (75n + bn)) % MOD;
  const p24 = (modPow(24n, bn - 1n) * (72n + 2n * bn)) % MOD;
  const p23 = (modPow(23n, bn - 1n) * (23n + bn)) % MOD;
  const ans = (((p26 - p25 + p24 - p23) % MOD) + MOD) % MOD;
  return Number(ans);
}

function stringCount(n) {
  return solve(n);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.stringCount = stringCount;
