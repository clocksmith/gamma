'use strict';

// 1941. Check if All Characters Have Equal Number of Occurrences (Easy).
// Specification: https://leetcode.com/problems/check-if-all-characters-have-equal-number-of-occurrences/description/
// O(n) time, O(1) alphabet space; s is nonempty and lowercase ASCII.
function solve(s) {
  const counts = new Array(26).fill(0);
  for (const character of s) counts[character.charCodeAt(0) - 97]++;
  let expected = 0;
  for (const count of counts) {
    if (count === 0) continue;
    if (expected === 0) expected = count;
    else if (count !== expected) return false;
  }
  return true;
}

const areOccurrencesEqual = solve;
class Solution {
  areOccurrencesEqual(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, areOccurrencesEqual };
