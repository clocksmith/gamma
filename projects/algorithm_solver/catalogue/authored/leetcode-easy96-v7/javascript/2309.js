'use strict';

// 2309. Greatest English Letter in Upper and Lower Case (Easy).
// Specification: https://leetcode.com/problems/greatest-english-letter-in-upper-and-lower-case/description/
// O(n) time, O(1) alphabet space; search Z through A for both cases.
function solve(s) {
  const present = new Set(s);
  for (let code = 90; code >= 65; code--) {
    const upper = String.fromCharCode(code);
    const lower = String.fromCharCode(code + 32);
    if (present.has(upper) && present.has(lower)) return upper;
  }
  return '';
}

const greatestLetter = solve;
class Solution {
  greatestLetter(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, greatestLetter };
