'use strict';

// 227. Basic Calculator II (Medium).
// Specification: https://leetcode.com/problems/basic-calculator-ii/description/
function solve(s) {
  const stack = [];
  let current = 0; let operation = '+';
  const text = s + '+';
  for (const ch of text) {
    if (ch >= '0' && ch <= '9') current = current * 10 + Number(ch);
    else if (ch === ' ') continue;
    else {
      if (operation === '+') stack.push(current);
      else if (operation === '-') stack.push(-current);
      else if (operation === '*') stack.push(stack.pop() * current);
      else if (operation === '/') stack.push(Math.trunc(stack.pop() / current));
      operation = ch; current = 0;
    }
  }
  return stack.reduce((sum, value) => sum + value, 0);
}
const calculate = solve;
class Solution { calculate(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, calculate };
