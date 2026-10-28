'use strict';

// 3346. Maximum Frequency of an Element After Performing Operations I (Medium).
// Specification: https://leetcode.com/problems/maximum-frequency-of-an-element-after-performing-operations-i/description/
function solve(nums, k, numOperations) {
  const cnt = new Map(); const diff = new Map();
  for (const x of nums) {
    cnt.set(x, (cnt.get(x) || 0) + 1);
    diff.set(x - k, (diff.get(x - k) || 0) + 1);
    diff.set(x + k + 1, (diff.get(x + k + 1) || 0) - 1);
  }
  const keys = [...new Set([...diff.keys(), ...cnt.keys()])].sort((a, b) => a - b);
  let s = 0; let ans = 0;
  for (const key of keys) {
    s += diff.get(key) || 0;
    ans = Math.max(ans, Math.min(s, (cnt.get(key) || 0) + numOperations));
  }
  return ans;
}
const maxFrequency = solve;
class Solution { maxFrequency(nums, k, numOperations) { return solve(nums, k, numOperations); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxFrequency };
