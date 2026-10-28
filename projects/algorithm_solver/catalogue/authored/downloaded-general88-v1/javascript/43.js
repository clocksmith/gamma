'use strict';

// 43. Multiply Strings (Medium).
// Specification: https://leetcode.com/problems/multiply-strings/description/
function solve(num1, num2) {
  if (num1 === '0' || num2 === '0') return '0';
  const result = new Array(num1.length + num2.length).fill(0);
  for (let i = num1.length - 1; i >= 0; i--) {
    for (let j = num2.length - 1; j >= 0; j--) {
      const product = Number(num1[i]) * Number(num2[j]) + result[i + j + 1];
      result[i + j + 1] = product % 10;
      result[i + j] += Math.floor(product / 10);
    }
  }
  let text = result.join('');
  while (text[0] === '0') text = text.slice(1);
  return text;
}
const multiply = solve;
class Solution { multiply(num1, num2) { return solve(num1, num2); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, multiply };
