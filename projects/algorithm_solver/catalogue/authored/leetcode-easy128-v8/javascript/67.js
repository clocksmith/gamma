'use strict';

// 67. Add Binary (Easy).
// Specification: https://leetcode.com/problems/add-binary/description/
// O(n + m) time and space; add digits without converting whole strings to integers.
function solve(a, b) {
  const result = [];
  let left = a.length - 1;
  let right = b.length - 1;
  let carry = 0;
  while (left >= 0 || right >= 0 || carry !== 0) {
    let total = carry;
    if (left >= 0) total += a.charCodeAt(left--) - 48;
    if (right >= 0) total += b.charCodeAt(right--) - 48;
    result.push(String(total % 2));
    carry = Math.floor(total / 2);
  }
  return result.reverse().join('');
}

const addBinary = solve;
class Solution {
  addBinary(a, b) { return solve(a, b); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, addBinary };
