'use strict';

// 3014. Minimum Number of Pushes to Type Word I (Easy).
// Specification: https://leetcode.com/problems/minimum-number-of-pushes-to-type-word-i/description/
// O(1) time and space; distinct letters fill eight keys at each press depth.
function solve(word) {
  const fullLevels = Math.floor(word.length / 8);
  const remainder = word.length % 8;
  return 4 * fullLevels * (fullLevels + 1) + remainder * (fullLevels + 1);
}

const minimumPushes = solve;
class Solution {
  minimumPushes(word) { return solve(word); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumPushes };
