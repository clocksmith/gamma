'use strict';

// 926. Flip String to Monotone Increasing (Medium).
// Specification: https://leetcode.com/problems/flip-string-to-monotone-increasing/description/
function solve(s) {
  let flips = 0; let ones = 0;
  for (const ch of s) {
    if (ch === '1') ones++;
    else flips = Math.min(flips + 1, ones);
  }
  return flips;
}
const minFlipsMonoIncr = solve;
class Solution { minFlipsMonoIncr(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minFlipsMonoIncr };
