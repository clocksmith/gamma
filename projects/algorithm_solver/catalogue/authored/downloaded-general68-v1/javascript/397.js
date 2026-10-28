'use strict';

// 397. Integer Replacement (Medium).
// Specification: https://leetcode.com/problems/integer-replacement/description/
function solve(n) {
  let steps = 0;
  let value = n;
  while (value !== 1) {
    if (value % 2 === 0) value = Math.floor(value / 2);
    else if (value === 3 || value % 4 === 1) value -= 1;
    else value += 1;
    steps++;
  }
  return steps;
}
const integerReplacement = solve;
class Solution { integerReplacement(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, integerReplacement };
