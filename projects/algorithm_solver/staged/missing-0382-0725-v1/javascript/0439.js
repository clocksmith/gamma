'use strict';

// 439. Ternary Expression Parser. Reduce right-associated ternary expressions from right to left.

function solve(expression) {
  const stack = [];
  for (let i = expression.length - 1; i >= 0; i -= 1) {
    const char = expression[i];
    if (stack.length > 0 && stack[stack.length - 1] === '?') {
      stack.pop();
      const yes = stack.pop();
      stack.pop();
      const no = stack.pop();
      stack.push(char === 'T' ? yes : no);
    } else stack.push(char);
  }
  return stack[stack.length - 1];
}

const parseTernary = solve;
class Solution {
  parseTernary(expression) { return solve(expression); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, parseTernary };
