'use strict';

// 324. Wiggle Sort II (Medium).
// Specification: https://leetcode.com/problems/wiggle-sort-ii/description/
function solve(nums) {
  const sorted = nums.slice().sort((a, b) => a - b);
  const n = sorted.length;
  const small = sorted.slice(0, Math.ceil(n / 2)).reverse();
  const large = sorted.slice(Math.ceil(n / 2)).reverse();
  const result = [];
  for (let i = 0; i < n; i++) result.push(i % 2 === 0 ? small[Math.floor(i / 2)] : large[Math.floor(i / 2)]);
  return result;
}
const wiggleSort = solve;
class Solution { wiggleSort(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, wiggleSort };
