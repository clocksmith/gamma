'use strict';

// 2546. Apply Bitwise Operations to Make Strings Equal: compare whether each string has a one that can generate and remove other bits.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(s, target) {
  return s.includes('1') === target.includes('1');
}

const makeStringsEqual = solve;
class Solution {
  makeStringsEqual(s, target) { return solve(s, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, makeStringsEqual };
