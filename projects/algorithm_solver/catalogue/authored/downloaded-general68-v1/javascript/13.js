'use strict';

// 13. Roman to Integer (Easy).
// Specification: https://leetcode.com/problems/roman-to-integer/description/
const VALUES = { I: 1, V: 5, X: 10, L: 50, C: 100, D: 500, M: 1000 };
function solve(s) {
  let total = 0;
  for (let i = 0; i < s.length; i++) {
    const value = VALUES[s[i]];
    const next = i + 1 < s.length ? VALUES[s[i + 1]] : 0;
    total += value < next ? -value : value;
  }
  return total;
}
const romanToInt = solve;
class Solution { romanToInt(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, romanToInt };
