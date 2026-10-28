'use strict';

// 2784. Check if Array is Good (Easy).
// Specification: https://leetcode.com/problems/check-if-array-is-good/description/
function solve(nums) {
  const n = nums.length - 1;
  if (n < 1) return false;
  const freq = new Map();
  for (const x of nums) freq.set(x, (freq.get(x) || 0) + 1);
  if (freq.size !== n) return false;
  for (let v = 1; v <= n; v++) {
    const want = v === n ? 2 : 1;
    if (freq.get(v) !== want) return false;
  }
  return true;
}
const isGood = solve;
class Solution { isGood(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, isGood };
