'use strict';

// 3823. Reverse Letters Then Special Characters in a String (Easy).
// Specification: https://leetcode.com/problems/reverse-letters-then-special-characters-in-a-string/description/
// O(n) time and space; preserve which positions hold lowercase letters versus special characters.
function solve(s) {
  const letters = [];
  const special = [];
  for (const character of s) {
    if (character >= 'a' && character <= 'z') letters.push(character);
    else special.push(character);
  }
  const result = [];
  for (const character of s) {
    if (character >= 'a' && character <= 'z') result.push(letters.pop());
    else result.push(special.pop());
  }
  return result.join('');
}

const reverseByType = solve;
class Solution {
  reverseByType(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, reverseByType };
