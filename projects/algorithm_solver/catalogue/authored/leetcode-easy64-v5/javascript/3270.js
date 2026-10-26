'use strict';

// 3270. Find the Key of the Numbers (Easy).
// Specification: https://leetcode.com/problems/find-the-key-of-the-numbers/description/
// O(1) time and space for four-digit inputs; implicit leading zeros participate.
function solve(num1, num2, num3) {
  let first = num1;
  let second = num2;
  let third = num3;
  let result = 0;
  for (let place = 1; place <= 1000; place *= 10) {
    result += Math.min(first % 10, second % 10, third % 10) * place;
    first = Math.floor(first / 10);
    second = Math.floor(second / 10);
    third = Math.floor(third / 10);
  }
  return result;
}

const generateKey = solve;
class Solution {
  generateKey(num1, num2, num3) { return solve(num1, num2, num3); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, generateKey };
