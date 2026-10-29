"use strict";
// Hack2Hire 67ccdb573363b83a81fc9983 (Pascal Triangle Encryption) over an INFERRED spec; qualification unknown.

const SMALL = [[1, 0, 0, 0, 0], [1, 1, 0, 0, 0], [1, 2, 1, 0, 0], [1, 3, 3, 1, 0], [1, 4, 6, 4, 1]];
const CRT = [[0, 6, 2, 8, 4], [5, 1, 7, 3, 9]];

function solve(digits) {
  const m = digits.length - 2;
  let first = 0, second = 0;
  for (let i = 0; i <= m; i++) {
    const odd = (i & m) === i ? 1 : 0;
    let r5 = 1, top = m, low = i;
    while (low || top) {
      const x = top % 5, y = low % 5;
      if (y > x) { r5 = 0; break; }
      r5 = (r5 * SMALL[x][y]) % 5;
      top = (top - x) / 5;
      low = (low - y) / 5;
    }
    const coef = CRT[odd][r5];
    if (coef) {
      first = (first + coef * (digits.charCodeAt(i) - 48)) % 10;
      second = (second + coef * (digits.charCodeAt(i + 1) - 48)) % 10;
    }
  }
  return String(first) + String(second);
}

function encrypt(digits) { return solve(digits); }

module.exports = solve;
module.exports.encrypt = encrypt;
