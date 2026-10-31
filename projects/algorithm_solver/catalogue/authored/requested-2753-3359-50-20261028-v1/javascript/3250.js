"use strict";

const MOD = 1000000007n;

function solve(nums) {
  const n = nums.length;
  let diffSum = 0;
  for (let i = 1; i < n; i++) {
    if (nums[i] > nums[i - 1]) diffSum += nums[i] - nums[i - 1];
  }
  const rem = nums[n - 1] - diffSum;
  if (rem < 0) return 0;
  let num = 1n;
  let den = 1n;
  const total = BigInt(rem + n);
  for (let i = 1n; i <= BigInt(n); i++) {
    num = (num * ((total - i + 1n) % MOD)) % MOD;
    den = (den * i) % MOD;
  }
  let inv = 1n;
  let b = den;
  let e = MOD - 2n;
  while (e > 0n) {
    if (e & 1n) inv = (inv * b) % MOD;
    b = (b * b) % MOD;
    e >>= 1n;
  }
  return Number((num * inv) % MOD);
}

function countOfPairs(nums) {
  return solve(nums);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.countOfPairs = countOfPairs;
