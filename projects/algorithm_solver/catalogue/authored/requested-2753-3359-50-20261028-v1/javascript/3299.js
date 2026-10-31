"use strict";

const MOD = 1000000007n;

function solve(nums) {
  function calc(step) {
    const cnt = new Map();
    const tot = new Map();
    let ans = 0n;
    for (let i = 0; i < nums.length; i++) {
      const x = nums[i];
      const bx = BigInt(x);
      const prevC = cnt.get(x - step) || 0n;
      const prevT = tot.get(x - step) || 0n;
      const nc = (1n + prevC) % MOD;
      const nt = (prevT + nc * bx) % MOD;
      ans = (ans + nt) % MOD;
      cnt.set(x, ((cnt.get(x) || 0n) + nc) % MOD);
      tot.set(x, ((tot.get(x) || 0n) + nt) % MOD);
    }
    return ans;
  }
  let base = 0n;
  for (let i = 0; i < nums.length; i++) base = (base + BigInt(nums[i])) % MOD;
  const res = (((calc(1) + calc(-1) - base) % MOD) + MOD) % MOD;
  return Number(res);
}

function getSum(nums) {
  return solve(nums);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.getSum = getSum;
