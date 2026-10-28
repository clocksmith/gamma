'use strict';

// 166. Fraction to Recurring Decimal (Medium).
// Specification: https://leetcode.com/problems/fraction-to-recurring-decimal/description/
function solve(numerator, denominator) {
  if (numerator === 0) return '0';
  let result = '';
  if ((numerator < 0) !== (denominator < 0)) result += '-';
  let num = Math.abs(numerator); let den = Math.abs(denominator);
  result += String(Math.floor(num / den));
  let remainder = num % den;
  if (remainder === 0) return result;
  result += '.';
  const seen = new Map();
  while (remainder !== 0) {
    if (seen.has(remainder)) {
      const index = seen.get(remainder);
      return result.slice(0, index) + '(' + result.slice(index) + ')';
    }
    seen.set(remainder, result.length);
    remainder *= 10;
    result += String(Math.floor(remainder / den));
    remainder %= den;
  }
  return result;
}
const fractionToDecimal = solve;
class Solution { fractionToDecimal(numerator, denominator) { return solve(numerator, denominator); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, fractionToDecimal };
