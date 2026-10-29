"use strict";
// Hack2Hire 69c0a3ed21f6ab42269647c2 (Fancy Number). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown.

function solve(n) {
  const digits = [];
  while (n > 0) {
    digits.push(n % 4);
    n = Math.floor(n / 4);
  }
  let count = 0;
  for (let position = digits.length - 1; position >= 0; position--) {
    const digit = digits[position];
    if (digit === 1) count += 2 ** position;
    else if (digit >= 2) {
      count += 2 ** (position + 1);
      break;
    }
  }
  return count - 1;
}

function countFancyNumbers(n) { return solve(n); }
module.exports = solve;
module.exports.countFancyNumbers = countFancyNumbers;
