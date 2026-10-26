'use strict';

// 1051. Height Checker (Easy).
// Specification: https://leetcode.com/problems/height-checker/description/
// O(n + 100) time, O(100) space; compare the original sequence with counting-sort order.
function solve(heights) {
  const counts = new Array(101).fill(0);
  for (const height of heights) counts[height]++;
  let expected = 1;
  let mismatches = 0;
  for (const height of heights) {
    while (counts[expected] === 0) expected++;
    if (height !== expected) mismatches++;
    counts[expected]--;
  }
  return mismatches;
}

const heightChecker = solve;
class Solution {
  heightChecker(heights) { return solve(heights); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, heightChecker };
