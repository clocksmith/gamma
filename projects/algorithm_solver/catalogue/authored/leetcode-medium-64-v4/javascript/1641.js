'use strict';

// 1641. Count Sorted Vowel Strings: count weak compositions of the length into five vowel multiplicities.
// O(1) time and O(1) auxiliary space on the declared n <= 50 domain; inputs are read-only.
function solve(n) {
  return (n + 1) * (n + 2) * (n + 3) * (n + 4) / 24;
}

const countVowelStrings = solve;
class Solution {
  countVowelStrings(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countVowelStrings };
