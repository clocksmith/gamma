'use strict';

// 592. Fraction Addition and Subtraction (Medium).
// Specification: https://leetcode.com/problems/fraction-addition-and-subtraction/description/
function gcd(a, b) { a = Math.abs(a); b = Math.abs(b); while (b !== 0) { const t = a % b; a = b; b = t; } return a; }
function solve(expression) {
  let numerator = 0; let denominator = 1;
  const tokens = expression.match(/[+-]?\d+\/\d+/g);
  for (const token of tokens) {
    const parts = token.split('/');
    const num = Number(parts[0]); const den = Number(parts[1]);
    numerator = numerator * den + num * denominator;
    denominator = denominator * den;
    const divisor = gcd(numerator, denominator);
    numerator = numerator / divisor; denominator = denominator / divisor;
  }
  if (denominator < 0) { numerator = -numerator; denominator = -denominator; }
  return numerator + '/' + denominator;
}
const fractionAddition = solve;
class Solution { fractionAddition(expression) { return solve(expression); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, fractionAddition };
