'use strict';

// 7. Reverse Integer (Easy).
// Specification: https://leetcode.com/problems/reverse-integer/description/
function solve(x) {
  let value = x < 0 ? x : -x;
  let result = 0;
  const lastDigit = x < 0 ? -8 : -7;
  while (value !== 0) {
    const quotient = Math.trunc(value / 10);
    const digit = value % 10;
    if (result < -214748364 || (result === -214748364 && digit < lastDigit)) return 0;
    result = result * 10 + digit;
    value = quotient;
  }
  return x < 0 ? result : -result;
}
const reverse = solve;
class Solution { reverse(x) { return solve(x); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, reverse };
