'use strict';

// 150. Evaluate Reverse Polish Notation (Medium).
// Specification: https://leetcode.com/problems/evaluate-reverse-polish-notation/description/
function solve(tokens) {
  const stack = [];
  for (const token of tokens) {
    if (token === '+' || token === '-' || token === '*' || token === '/') {
      const b = stack.pop(); const a = stack.pop();
      let value = 0;
      if (token === '+') value = a + b;
      else if (token === '-') value = a - b;
      else if (token === '*') value = a * b;
      else value = Math.trunc(a / b);
      stack.push(value);
    } else stack.push(parseInt(token, 10));
  }
  return stack[0];
}
const evalRPN = solve;
class Solution { evalRPN(tokens) { return solve(tokens); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, evalRPN };
