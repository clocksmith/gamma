'use strict';

// 7. Reverse Integer (Easy).
// Specification: https://leetcode.com/problems/reverse-integer/description/
function solve(x) {
  let result = 0;
  let value = x;
  while (value !== 0) {
    const digit = value % 10;
    result = result * 10 + digit;
    value = Math.trunc(value / 10);
  }
  if (result > 2147483647 || result < -2147483648) return 0;
  return result;
}
const reverse = solve;
class Solution { reverse(x) { return solve(x); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, reverse };
