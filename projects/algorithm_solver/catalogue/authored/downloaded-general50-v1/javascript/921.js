'use strict';

// 921. Minimum Add to Make Parentheses Valid (Medium).
// Specification: https://leetcode.com/problems/minimum-add-to-make-parentheses-valid/description/
function solve(s) {
  let open = 0; let needed = 0;
  for (const ch of s) {
    if (ch === '(') open++;
    else if (open > 0) open--;
    else needed++;
  }
  return open + needed;
}
const minAddToMakeValid = solve;
class Solution { minAddToMakeValid(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minAddToMakeValid };
