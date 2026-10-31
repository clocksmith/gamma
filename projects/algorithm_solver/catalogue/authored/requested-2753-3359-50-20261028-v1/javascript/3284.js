"use strict";

const MOD = 1000000007n;

function solve(nums) {
  function runDir(step) {
    let total = 0n;
    let cnt = 0n;
    let curSum = 0n;
    for (let i = 0; i < nums.length; i++) {
      const x = BigInt(nums[i]);
      if (i > 0 && nums[i] - nums[i - 1] === step) {
        cnt += 1n;
        curSum = (curSum + cnt * x) % MOD;
      } else {
        cnt = 1n;
        curSum = ((x % MOD) + MOD) % MOD;
      }
      total = (total + curSum) % MOD;
    }
    return total;
  }
  let baseSum = 0n;
  for (let i = 0; i < nums.length; i++) baseSum = (baseSum + BigInt(nums[i])) % MOD;
  const ans = (((runDir(1) + runDir(-1) - baseSum) % MOD) + MOD) % MOD;
  return Number(ans);
}

function getSum(nums) {
  return solve(nums);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.getSum = getSum;
