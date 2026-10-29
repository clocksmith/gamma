"use strict";
// Hack2Hire 677c8aba5cbaff553b53b06e (Subset Sum Equals K) over an INFERRED spec; qualification unknown.

function solve(nums, k) {
  let total = 0;
  for (const x of nums) total += x;
  if (k > total) return false;
  const target = Math.min(k, total - k), bigTarget = BigInt(target);
  const mask = (1n << (bigTarget + 1n)) - 1n;
  let reach = 1n;
  for (const x of nums) {
    if (x <= target) {
      reach |= (reach << BigInt(x)) & mask;
      if ((reach >> bigTarget) & 1n) return true;
    }
  }
  return ((reach >> bigTarget) & 1n) === 1n;
}

function subsetSumExists(nums, k) { return solve(nums, k); }

module.exports = solve;
module.exports.subsetSumExists = subsetSumExists;
