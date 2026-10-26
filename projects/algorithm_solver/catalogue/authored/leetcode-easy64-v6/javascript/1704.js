'use strict';

// 1704. Determine if String Halves Are Alike (Easy).
// Specification: https://leetcode.com/problems/determine-if-string-halves-are-alike/description/
// O(n) time, O(1) space; recognize both uppercase and lowercase ASCII vowels.
function solve(s) {
  const vowels = 'aeiouAEIOU';
  const half = s.length / 2;
  let balance = 0;
  for (let index = 0; index < s.length; index++) {
    if (vowels.includes(s[index])) balance += index < half ? 1 : -1;
  }
  return balance === 0;
}

const halvesAreAlike = solve;
class Solution {
  halvesAreAlike(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, halvesAreAlike };
