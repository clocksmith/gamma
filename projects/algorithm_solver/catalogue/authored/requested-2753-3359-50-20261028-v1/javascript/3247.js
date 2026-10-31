"use strict";

const MOD = 1000000007n;

function solve(nums) {
  let hasOdd = false;
  for (let i = 0; i < nums.length; i++) {
    if ((nums[i] & 1) !== 0) {
      hasOdd = true;
      break;
    }
  }
  if (!hasOdd) return 0;
  let res = 1n;
  let b = 2n;
  let e = BigInt(nums.length - 1);
  while (e > 0n) {
    if (e & 1n) res = (res * b) % MOD;
    b = (b * b) % MOD;
    e >>= 1n;
  }
  return Number(res);
}

function subsequenceCount(nums) {
  return solve(nums);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.subsequenceCount = subsequenceCount;
