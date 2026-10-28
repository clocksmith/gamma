'use strict';

// 1745. Palindrome Partitioning IV (Hard).
// Specification: https://leetcode.com/problems/palindrome-partitioning-iv/description/
function solve(s) {
  const n = s.length;
  const pal = Array.from({ length: n }, () => new Array(n).fill(false));
  for (let i = n - 1; i >= 0; i--) {
    for (let j = i; j < n; j++) {
      pal[i][j] = s[i] === s[j] && (j - i < 2 || pal[i + 1][j - 1]);
    }
  }
  for (let i = 0; i < n - 2; i++) {
    if (!pal[0][i]) continue;
    for (let j = i + 1; j < n - 1; j++) {
      if (pal[i + 1][j] && pal[j + 1][n - 1]) return true;
    }
  }
  return false;
}
const checkPartitioning = solve;
class Solution { checkPartitioning(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkPartitioning };
