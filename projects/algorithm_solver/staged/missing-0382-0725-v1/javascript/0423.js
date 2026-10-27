'use strict';

// 423. Reconstruct Original Digits from English.

function solve(s) {
  const c = Object.create(null);
  for (const char of s) c[char] = (c[char] || 0) + 1;
  const count = char => c[char] || 0;
  const d = Array(10).fill(0);
  d[0] = count('z'); d[2] = count('w'); d[4] = count('u'); d[6] = count('x'); d[8] = count('g');
  d[3] = count('h') - d[8]; d[5] = count('f') - d[4]; d[7] = count('s') - d[6];
  d[1] = count('o') - d[0] - d[2] - d[4]; d[9] = count('i') - d[5] - d[6] - d[8];
  return d.map((amount, digit) => String(digit).repeat(amount)).join('');
}

const originalDigits = solve;
class Solution {
  originalDigits(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, originalDigits };
