'use strict';

// 1375. Number of Times Binary String Is Prefix-Aligned (Medium).
// Specification: https://leetcode.com/problems/number-of-times-binary-string-is-prefix-aligned/description/
function solve(flips) {
  let best = 0; let count = 0;
  for (let i = 0; i < flips.length; i++) {
    best = Math.max(best, flips[i]);
    if (best === i + 1) count++;
  }
  return count;
}
const numTimesAllBlue = solve;
class Solution { numTimesAllBlue(...args) { return solve(...args); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numTimesAllBlue };
