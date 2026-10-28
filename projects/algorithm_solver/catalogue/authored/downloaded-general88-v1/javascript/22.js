'use strict';

// 22. Generate Parentheses (Medium).
// Specification: https://leetcode.com/problems/generate-parentheses/description/
function solve(n) {
  const result = [];
  function backtrack(current, open, close) {
    if (current.length === 2 * n) { result.push(current); return; }
    if (open < n) backtrack(current + '(', open + 1, close);
    if (close < open) backtrack(current + ')', open, close + 1);
  }
  backtrack('', 0, 0);
  return result;
}
const generateParenthesis = solve;
class Solution { generateParenthesis(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, generateParenthesis };
