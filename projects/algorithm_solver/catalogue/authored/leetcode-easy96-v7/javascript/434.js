'use strict';

// 434. Number of Segments in a String (Easy).
// Specification: https://leetcode.com/problems/number-of-segments-in-a-string/description/
// O(n) time, O(1) space; segments are maximal non-space runs.
function solve(s) {
  let count = 0;
  for (let index = 0; index < s.length; index++) {
    if (s[index] !== ' ' && (index === 0 || s[index - 1] === ' ')) count++;
  }
  return count;
}

const countSegments = solve;
class Solution {
  countSegments(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countSegments };
