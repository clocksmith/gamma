'use strict';

// 2485. Find the Pivot Integer (Easy).
// Specification: https://leetcode.com/problems/find-the-pivot-integer/description/
// O(1) time and space in the bounded domain; a pivot squares to n*(n+1)/2.
function solve(n) {
  const total = n * (n + 1) / 2;
  const pivot = Math.floor(Math.sqrt(total));
  return pivot * pivot === total ? pivot : -1;
}

const pivotInteger = solve;
class Solution {
  pivotInteger(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, pivotInteger };
