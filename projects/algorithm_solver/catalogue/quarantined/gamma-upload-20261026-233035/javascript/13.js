'use strict';
// 13. Roman to Integer.
function solve(s) {
  const values = { I: 1, V: 5, X: 10, L: 50, C: 100, D: 500, M: 1000 };
  let total = 0;
  for (let index = 0; index < s.length; index += 1) {
    const value = values[s[index]];
    total += index + 1 < s.length && value < values[s[index + 1]] ? -value : value;
  }
  return total;
}
const romanToInt = solve;
class Solution { romanToInt(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, romanToInt };
