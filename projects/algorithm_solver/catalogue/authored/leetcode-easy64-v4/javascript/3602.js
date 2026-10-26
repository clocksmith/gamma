'use strict';

// 3602. Hexadecimal and Hexatrigesimal Conversion (Easy).
// Specification: https://leetcode.com/problems/hexadecimal-and-hexatrigesimal-conversion/description/
// O(log n) time and space; n <= 1000 keeps both powers exactly representable.
function solve(n) {
  const alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  function encode(value, base) {
    const digits = [];
    while (value > 0) {
      digits.push(alphabet[value % base]);
      value = Math.floor(value / base);
    }
    return digits.reverse().join('');
  }
  return encode(n * n, 16) + encode(n * n * n, 36);
}

const concatHex36 = solve;
class Solution {
  concatHex36(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, concatHex36 };
