'use strict';

// 1271. Hexspeak (Easy).
// Specification: https://leetcode.com/problems/hexspeak/description/
function solve(num) {
  const hex = num.toString(16).toUpperCase();
  let result = '';
  for (const ch of hex) {
    if (ch === '0') result += 'O';
    else if (ch === '1') result += 'I';
    else if (ch >= 'A' && ch <= 'F') result += ch;
    else return 'ERROR';
  }
  return result;
}
const toHexspeak = solve;
class Solution { toHexspeak(num) { return solve(num); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, toHexspeak };
