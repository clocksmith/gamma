'use strict';

// 1906. Minimum Absolute Difference Queries (Medium).
// Specification: https://leetcode.com/problems/minimum-absolute-difference-queries/description/
function solve(nums, queries) {
  const n = nums.length; const pref = [];
  pref.push(new Array(101).fill(0));
  for (let i = 0; i < n; i++) {
    const row = pref[i].slice(); row[nums[i]]++; pref.push(row);
  }
  const out = [];
  for (const q of queries) {
    const left = q[0]; const right = q[1]; let prev = -1; let best = -1;
    for (let v = 1; v <= 100; v++) {
      if (pref[right + 1][v] - pref[left][v] > 0) {
        if (prev !== -1 && (best === -1 || v - prev < best)) best = v - prev;
        prev = v;
      }
    }
    out.push(best);
  }
  return out;
}
const minDifference = solve;
class Solution { minDifference(nums, queries) { return solve(nums, queries); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minDifference };
