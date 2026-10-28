'use strict';

// 2481. Minimum Cuts to Divide a Circle (Easy).
// Specification: https://leetcode.com/problems/minimum-cuts-to-divide-a-circle/description/
function solve(n) {
  if (n === 1) return 0;
  return n % 2 === 0 ? n / 2 : n;
}
const numberOfCuts = solve;
class Solution { numberOfCuts(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfCuts };
