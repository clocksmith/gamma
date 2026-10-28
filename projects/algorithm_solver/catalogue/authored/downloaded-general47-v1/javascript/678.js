'use strict';

// 678. Valid Parenthesis String (Medium).
// Specification: https://leetcode.com/problems/valid-parenthesis-string/description/
function solve(s) {
  let low = 0; let high = 0;
  for (const ch of s) {
    if (ch === '(') { low++; high++; }
    else if (ch === ')') { low--; high--; }
    else { low--; high++; }
    if (high < 0) return false;
    low = Math.max(low, 0);
  }
  return low === 0;
}
const checkValidString = solve;
class Solution { checkValidString(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkValidString };
