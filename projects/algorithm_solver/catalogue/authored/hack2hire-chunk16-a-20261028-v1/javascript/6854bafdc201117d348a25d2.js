"use strict";
// Hack2Hire 6854bafdc201117d348a25d2 (Maximize Number With K Swaps) over an INFERRED spec; qualification unknown.

function solve(s, k) {
  const digits = s.split('');
  let left = k;
  for (let i = 0; i < digits.length && left > 0; i++) {
    if (digits[i] < '5') { digits[i] = '5'; left--; }
  }
  return digits.join('');
}

function maximizeNumber(s, k) { return solve(s, k); }

module.exports = solve;
module.exports.maximizeNumber = maximizeNumber;
