'use strict';

// 241. Different Ways to Add Parentheses (Medium).
// Specification: https://leetcode.com/problems/different-ways-to-add-parentheses/description/
function solve(expression) {
  const result = [];
  for (let i = 0; i < expression.length; i++) {
    const ch = expression[i];
    if (ch === '+' || ch === '-' || ch === '*') {
      const left = solve(expression.slice(0, i));
      const right = solve(expression.slice(i + 1));
      for (const a of left) { for (const b of right) { if (ch === '+') result.push(a + b); else if (ch === '-') result.push(a - b); else result.push(a * b); } }
    }
  }
  if (result.length === 0) result.push(Number(expression));
  return result.sort((a, b) => a - b);
}
const diffWaysToCompute = solve;
class Solution { diffWaysToCompute(expression) { return solve(expression); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, diffWaysToCompute };
