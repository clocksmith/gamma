"use strict";
// Hack2Hire 677c90795cbaff553b53b06f (Subset Sum Equals K) over an INFERRED spec; qualification unknown.

const MOD = 1000000007;

function solve(nums, k) {
  let total = 0;
  for (const x of nums) total += x;
  if (k > total) return 0;
  const target = Math.min(k, total - k), ways = new Int32Array(target + 1);
  ways[0] = 1;
  let reach = 0;
  for (const x of nums) {
    reach = Math.min(target, reach + x);
    for (let s = reach; s >= x; s--) {
      const v = ways[s] + ways[s - x];
      ways[s] = v >= MOD ? v - MOD : v;
    }
  }
  return ways[target];
}

function countSubsets(nums, k) { return solve(nums, k); }

module.exports = solve;
module.exports.countSubsets = countSubsets;
