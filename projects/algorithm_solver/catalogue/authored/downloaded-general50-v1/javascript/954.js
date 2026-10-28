'use strict';

// 954. Array of Doubled Pairs (Medium).
// Specification: https://leetcode.com/problems/array-of-doubled-pairs/description/
function solve(arr) {
  const counts = new Map();
  for (const v of arr) counts.set(v, (counts.get(v) || 0) + 1);
  const keys = [...counts.keys()].sort((a, b) => Math.abs(a) - Math.abs(b));
  for (const x of keys) {
    const need = counts.get(x);
    if (need === 0) continue;
    if ((counts.get(2 * x) || 0) < need) return false;
    counts.set(2 * x, counts.get(2 * x) - need);
  }
  return true;
}
const canReorderDoubled = solve;
class Solution { canReorderDoubled(arr) { return solve(arr); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, canReorderDoubled };
