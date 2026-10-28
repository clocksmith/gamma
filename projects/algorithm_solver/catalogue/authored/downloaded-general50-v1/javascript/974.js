'use strict';

// 974. Subarray Sums Divisible by K (Medium).
// Specification: https://leetcode.com/problems/subarray-sums-divisible-by-k/description/
function solve(nums, k) {
  const counts = new Map([[0, 1]]);
  let prefix = 0; let total = 0;
  for (const v of nums) {
    prefix = (prefix + v) % k;
    if (prefix < 0) prefix += k;
    total += counts.get(prefix) || 0;
    counts.set(prefix, (counts.get(prefix) || 0) + 1);
  }
  return total;
}
const subarraysDivByK = solve;
class Solution { subarraysDivByK(nums, k) { return solve(nums, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, subarraysDivByK };
