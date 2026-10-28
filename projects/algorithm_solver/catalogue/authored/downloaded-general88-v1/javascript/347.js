'use strict';

// 347. Top K Frequent Elements (Medium).
// Specification: https://leetcode.com/problems/top-k-frequent-elements/description/
function solve(nums, k) {
  const counts = new Map();
  for (const value of nums) counts.set(value, (counts.get(value) || 0) + 1);
  const entries = [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0] - b[0]);
  return entries.slice(0, k).map(([value]) => value);
}
const topKFrequent = solve;
class Solution { topKFrequent(nums, k) { return solve(nums, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, topKFrequent };
