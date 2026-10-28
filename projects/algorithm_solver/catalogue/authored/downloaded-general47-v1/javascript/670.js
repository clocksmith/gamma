'use strict';

// 670. Maximum Swap (Medium).
// Specification: https://leetcode.com/problems/maximum-swap/description/
function solve(num) {
  const digits = String(num).split('').map(Number);
  const last = new Array(10).fill(-1);
  for (let i = 0; i < digits.length; i++) last[digits[i]] = i;
  for (let i = 0; i < digits.length; i++) {
    for (let digit = 9; digit > digits[i]; digit--) {
      if (last[digit] > i) {
        const tmp = digits[i]; digits[i] = digits[last[digit]]; digits[last[digit]] = tmp;
        return Number(digits.join(''));
      }
    }
  }
  return num;
}
const maximumSwap = solve;
class Solution { maximumSwap(num) { return solve(num); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumSwap };
