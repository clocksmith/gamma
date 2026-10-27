'use strict';

// 393. UTF-8 Validation. Validate the problem's byte-prefix structure, not Unicode scalar canonicality.

function solve(data) {
  let remaining = 0;
  for (let value of data) {
    value &= 255;
    if (remaining > 0) {
      if ((value >> 6) !== 2) return false;
      remaining -= 1;
    } else if (value < 128) {
      continue;
    } else if ((value >> 5) === 6) {
      remaining = 1;
    } else if ((value >> 4) === 14) {
      remaining = 2;
    } else if ((value >> 3) === 30) {
      remaining = 3;
    } else return false;
  }
  return remaining === 0;
}

const validUtf8 = solve;
class Solution {
  validUtf8(data) { return solve(data); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, validUtf8 };
