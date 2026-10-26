'use strict';

// 806. Number of Lines To Write String (Easy).
// Specification: https://leetcode.com/problems/number-of-lines-to-write-string/description/
// O(n) time, O(1) space; wrap before a letter would exceed 100 units.
function solve(widths, s) {
  let lines = 1;
  let used = 0;
  for (const character of s) {
    const width = widths[character.charCodeAt(0) - 97];
    if (used + width > 100) {
      lines++;
      used = 0;
    }
    used += width;
  }
  return [lines, used];
}

const numberOfLines = solve;
class Solution {
  numberOfLines(widths, s) { return solve(widths, s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfLines };
