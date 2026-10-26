'use strict';

// 415. Add Strings (Easy).
// Specification: https://leetcode.com/problems/add-strings/description/
// O(n + m) time and output space; decimal carry arithmetic without whole-string conversion.
function solve(num1, num2) {
  let first = num1.length - 1;
  let second = num2.length - 1;
  let carry = 0;
  const digits = [];
  while (first >= 0 || second >= 0 || carry > 0) {
    let total = carry;
    if (first >= 0) total += num1.charCodeAt(first--) - 48;
    if (second >= 0) total += num2.charCodeAt(second--) - 48;
    digits.push(String(total % 10));
    carry = Math.floor(total / 10);
  }
  return digits.reverse().join('');
}

const addStrings = solve;
class Solution {
  addStrings(num1, num2) { return solve(num1, num2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, addStrings };
