'use strict';

// 1869. Longer Contiguous Segments of Ones than Zeros (Easy).
// Specification: https://leetcode.com/problems/longer-contiguous-segments-of-ones-than-zeros/description/
function longestRun(s, target) {
  let best = 0; let current = 0;
  for (const ch of s) {
    if (ch === target) { current++; best = Math.max(best, current); }
    else current = 0;
  }
  return best;
}
function solve(s) {
  return longestRun(s, '1') > longestRun(s, '0');
}
const checkZeroOnes = solve;
class Solution { checkZeroOnes(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkZeroOnes };
