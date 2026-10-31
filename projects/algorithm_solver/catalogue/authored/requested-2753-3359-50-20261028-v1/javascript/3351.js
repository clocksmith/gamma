"use strict";

const MOD = 1000000007n;

function solve(nums) {
  const cnt = new Map();
  const tot = new Map();
  for (let i = 0; i < nums.length; i++) {
    const x = nums[i];
    const bx = BigInt(x);
    const cm = cnt.get(x - 1) || 0n;
    const cp = cnt.get(x + 1) || 0n;
    const tm = tot.get(x - 1) || 0n;
    const tp = tot.get(x + 1) || 0n;
    const nc = (1n + cm + cp) % MOD;
    const nt = (tm + tp + nc * bx) % MOD;
    cnt.set(x, ((cnt.get(x) || 0n) + nc) % MOD);
    tot.set(x, ((tot.get(x) || 0n) + nt) % MOD);
  }
  let ans = 0n;
  for (const v of tot.values()) ans = (ans + v) % MOD;
  return Number(ans);
}

function sumOfGoodSubsequences(nums) {
  return solve(nums);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.sumOfGoodSubsequences = sumOfGoodSubsequences;
