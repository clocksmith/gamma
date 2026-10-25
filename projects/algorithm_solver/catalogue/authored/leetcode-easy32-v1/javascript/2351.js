'use strict';

// 2351. First Letter to Appear Twice (Easy).
// Specification: https://leetcode.com/problems/first-letter-to-appear-twice/description/
// O(n) time, O(1) alphabet space. A repeated lowercase letter is guaranteed.
function solve(s) {
  const seen = new Array(26).fill(false);
  for (const character of s) {
    const index = character.charCodeAt(0) - 97;
    if (seen[index]) return character;
    seen[index] = true;
  }
  return '';
}

const repeatedCharacter = solve;
class Solution {
  repeatedCharacter(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, repeatedCharacter };
