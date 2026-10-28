'use strict';

// 856. Score of Parentheses (Medium).
// Specification: https://leetcode.com/problems/score-of-parentheses/description/
function solve(s) {
  const stack = [0];
  for (const ch of s) {
    if (ch === '(') stack.push(0);
    else { const v = stack.pop(); stack[stack.length - 1] += Math.max(2 * v, 1); }
  }
  return stack[0];
}
const scoreOfParentheses = solve;
class Solution { scoreOfParentheses(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, scoreOfParentheses };
