'use strict';

// 1790. Check if One String Swap Can Make Strings Equal (Easy).
// Specification: https://leetcode.com/problems/check-if-one-string-swap-can-make-strings-equal/description/
// O(n) time, O(1) space; zero mismatches or one crossed pair permits at most one swap.
function solve(s1, s2) {
  let firstMismatch = -1;
  let secondMismatch = -1;
  for (let index = 0; index < s1.length; index++) {
    if (s1[index] === s2[index]) continue;
    if (firstMismatch === -1) firstMismatch = index;
    else if (secondMismatch === -1) secondMismatch = index;
    else return false;
  }
  if (firstMismatch === -1) return true;
  if (secondMismatch === -1) return false;
  return s1[firstMismatch] === s2[secondMismatch] && s1[secondMismatch] === s2[firstMismatch];
}

const areAlmostEqual = solve;
class Solution {
  areAlmostEqual(s1, s2) { return solve(s1, s2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, areAlmostEqual };
