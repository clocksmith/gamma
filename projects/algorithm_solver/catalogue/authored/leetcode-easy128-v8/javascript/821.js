'use strict';

// 821. Shortest Distance to a Character (Easy).
// Specification: https://leetcode.com/problems/shortest-distance-to-a-character/description/
// O(n) time and output space; combine nearest occurrences from both directions.
function solve(s, c) {
  const result = new Array(s.length);
  let nearest = -s.length;
  for (let index = 0; index < s.length; index++) {
    if (s[index] === c) nearest = index;
    result[index] = index - nearest;
  }
  nearest = 2 * s.length;
  for (let index = s.length - 1; index >= 0; index--) {
    if (s[index] === c) nearest = index;
    result[index] = Math.min(result[index], nearest - index);
  }
  return result;
}

const shortestToChar = solve;
class Solution {
  shortestToChar(s, c) { return solve(s, c); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, shortestToChar };
