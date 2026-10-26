'use strict';

// 387. First Unique Character in a String (Easy).
// Specification: https://leetcode.com/problems/first-unique-character-in-a-string/description/
// O(n) time, O(1) space for lowercase-English input; preserve original indices.
function solve(s) {
  const counts = new Array(26).fill(0);
  for (const character of s) counts[character.charCodeAt(0) - 97]++;
  for (let index = 0; index < s.length; index++) {
    if (counts[s.charCodeAt(index) - 97] === 1) return index;
  }
  return -1;
}

const firstUniqChar = solve;
class Solution {
  firstUniqChar(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, firstUniqChar };
