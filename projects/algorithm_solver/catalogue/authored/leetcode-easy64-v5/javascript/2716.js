'use strict';

// 2716. Minimize String Length (Easy).
// Specification: https://leetcode.com/problems/minimize-string-length/description/
// O(n) time, O(1) space for the lowercase English alphabet.
function solve(s) {
  return new Set(s).size;
}

const minimizedStringLength = solve;
class Solution {
  minimizedStringLength(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimizedStringLength };
