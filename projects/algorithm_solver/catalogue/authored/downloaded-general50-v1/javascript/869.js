'use strict';

// 869. Reordered Power of 2 (Medium).
// Specification: https://leetcode.com/problems/reordered-power-of-2/description/
function signature(x) { return [...String(x)].sort().join(''); }
function solve(n) {
  const target = signature(n);
  for (let power = 1; power <= 1000000000; power *= 2) { if (signature(power) === target) return true; }
  return false;
}
const reorderedPowerOf2 = solve;
class Solution { reorderedPowerOf2(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, reorderedPowerOf2 };
