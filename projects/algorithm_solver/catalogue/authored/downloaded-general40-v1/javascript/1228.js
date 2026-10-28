'use strict';

// 1228. Missing Number In Arithmetic Progression (Easy).
// Specification: https://leetcode.com/problems/missing-number-in-arithmetic-progression/description/
function solve(arr) {
  const sorted = arr.slice().sort((a, b) => a - b);
  const step = Math.floor((sorted[sorted.length - 1] - sorted[0]) / sorted.length);
  for (let i = 0; i < sorted.length - 1; i++) { if (sorted[i + 1] - sorted[i] !== step) return sorted[i] + step; }
  return sorted[sorted.length - 1] + step;
}
const missingNumber = solve;
class Solution { missingNumber(arr) { return solve(arr); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, missingNumber };
