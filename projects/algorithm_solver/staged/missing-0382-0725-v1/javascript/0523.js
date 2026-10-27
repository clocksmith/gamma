'use strict';

// 523. Continuous Subarray Sum.

function solve(nums, k) {
  const first = new Map([[0, -1]]);
  let total = 0;
  for (let i = 0; i < nums.length; i += 1) {
    total += nums[i];
    const remainder = k === 0 ? total : ((total % Math.abs(k)) + Math.abs(k)) % Math.abs(k);
    if (first.has(remainder)) { if (i - first.get(remainder) >= 2) return true; }
    else first.set(remainder, i);
  }
  return false;
}

const checkSubarraySum = solve;
class Solution {
  checkSubarraySum(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkSubarraySum };
