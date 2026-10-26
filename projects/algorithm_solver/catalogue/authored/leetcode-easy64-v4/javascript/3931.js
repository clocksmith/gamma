'use strict';

// 3931. Check Adjacent Digit Differences (Easy).
// Specification: https://leetcode.com/problems/check-adjacent-digit-differences/description/
// O(n) time, O(1) space; compare adjacent ASCII decimal digits.
function solve(s) {
  for (let index = 1; index < s.length; index++) {
    if (Math.abs(s.charCodeAt(index) - s.charCodeAt(index - 1)) > 2) return false;
  }
  return true;
}

const isAdjacentDiffAtMostTwo = solve;
class Solution {
  isAdjacentDiffAtMostTwo(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isAdjacentDiffAtMostTwo };
