'use strict';

// 848. Shifting Letters (Medium).
// Specification: https://leetcode.com/problems/shifting-letters/description/
function solve(s, shifts) {
  const chars = [...s];
  let total = 0;
  for (let i = s.length - 1; i >= 0; i--) {
    total = (total + shifts[i]) % 26;
    chars[i] = String.fromCharCode(97 + (chars[i].charCodeAt(0) - 97 + total) % 26);
  }
  return chars.join('');
}
const shiftingLetters = solve;
class Solution { shiftingLetters(s, shifts) { return solve(s, shifts); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, shiftingLetters };
