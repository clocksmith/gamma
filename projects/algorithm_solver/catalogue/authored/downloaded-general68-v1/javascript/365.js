'use strict';

// 365. Water and Jug Problem (Medium).
// Specification: https://leetcode.com/problems/water-and-jug-problem/description/
function gcd(a, b) { while (b !== 0) { const t = a % b; a = b; b = t; } return a; }
function solve(x, y, target) {
  if (target === 0) return true;
  if (x + y < target) return false;
  return target % gcd(x, y) === 0;
}
const canMeasureWater = solve;
class Solution { canMeasureWater(x, y, target) { return solve(x, y, target); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, canMeasureWater };
