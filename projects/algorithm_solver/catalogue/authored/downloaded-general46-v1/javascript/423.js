'use strict';

// 423. Reconstruct Original Digits from English (Medium).
// Specification: https://leetcode.com/problems/reconstruct-original-digits-from-english/description/
function solve(s) {
  const counts = {};
  for (const ch of s) counts[ch] = (counts[ch] || 0) + 1;
  const digits = new Array(10).fill(0);
  digits[0] = counts['z'] || 0;
  digits[2] = counts['w'] || 0;
  digits[4] = counts['u'] || 0;
  digits[6] = counts['x'] || 0;
  digits[8] = counts['g'] || 0;
  digits[3] = (counts['h'] || 0) - digits[8];
  digits[5] = (counts['f'] || 0) - digits[4];
  digits[7] = (counts['s'] || 0) - digits[6];
  digits[1] = (counts['o'] || 0) - digits[0] - digits[2] - digits[4];
  digits[9] = (counts['i'] || 0) - digits[5] - digits[6] - digits[8];
  let result = '';
  for (let d = 0; d <= 9; d++) result += String(d).repeat(digits[d]);
  return result;
}
const originalDigits = solve;
class Solution { originalDigits(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, originalDigits };
