'use strict';

// 393. UTF-8 Validation (Medium).
// Specification: https://leetcode.com/problems/utf-8-validation/description/
function solve(data) {
  let remaining = 0;
  for (const byte of data) {
    if (remaining === 0) {
      if ((byte >> 5) === 0b110) remaining = 1;
      else if ((byte >> 4) === 0b1110) remaining = 2;
      else if ((byte >> 3) === 0b11110) remaining = 3;
      else if ((byte >> 7) !== 0) return false;
    } else {
      if ((byte >> 6) !== 0b10) return false;
      remaining--;
    }
  }
  return remaining === 0;
}
const validUtf8 = solve;
class Solution { validUtf8(data) { return solve(data); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, validUtf8 };
