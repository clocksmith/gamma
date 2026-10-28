'use strict';

// 1190. Reverse Substrings Between Each Pair of Parentheses (Medium).
// Specification: https://leetcode.com/problems/reverse-substrings-between-each-pair-of-parentheses/description/
function solve(s) {
  const stack = [''];
  for (const ch of s) {
    if (ch === '(') stack.push('');
    else if (ch === ')') { const top = stack.pop().split('').reverse().join(''); stack[stack.length - 1] += top; }
    else stack[stack.length - 1] += ch;
  }
  return stack[0];
}
const reverseParentheses = solve;
class Solution { reverseParentheses(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, reverseParentheses };
