'use strict';

// 3750. Minimum Number of Flips to Reverse Binary String (Easy).
// Specification: https://leetcode.com/problems/minimum-number-of-flips-to-reverse-binary-string/description/
// O(log n) time and space; count mismatches with the original reversed representation.
function solve(n) {
  const digits = n.toString(2);
  let flips = 0;
  for (let index = 0; index < digits.length; index++) {
    if (digits[index] !== digits[digits.length - 1 - index]) flips++;
  }
  return flips;
}

const minimumFlips = solve;
class Solution {
  minimumFlips(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumFlips };
