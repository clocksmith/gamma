'use strict';

// 1541. Minimum Insertions to Balance a Parentheses String: track required closing parentheses in adjacent pairs.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(s) {
  let needed = 0;
  let inserted = 0;
  for (const character of s) {
    if (character === '(') {
      if (needed % 2) {
        inserted += 1;
        needed -= 1;
      }
      needed += 2;
    } else {
      needed -= 1;
      if (needed < 0) {
        inserted += 1;
        needed = 1;
      }
    }
  }
  return inserted + needed;
}

const minInsertions = solve;
class Solution {
  minInsertions(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minInsertions };
