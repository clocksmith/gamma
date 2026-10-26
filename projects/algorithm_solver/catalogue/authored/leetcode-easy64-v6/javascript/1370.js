'use strict';

// 1370. Increasing Decreasing String (Easy).
// Specification: https://leetcode.com/problems/increasing-decreasing-string/description/
// O(n) time for the fixed 26-letter alphabet, O(n) result space.
function solve(s) {
  const counts = new Array(26).fill(0);
  for (const character of s) counts[character.charCodeAt(0) - 97]++;
  const result = [];
  while (result.length < s.length) {
    for (let letter = 0; letter < 26; letter++) {
      if (counts[letter] > 0) {
        result.push(String.fromCharCode(97 + letter));
        counts[letter]--;
      }
    }
    for (let letter = 25; letter >= 0; letter--) {
      if (counts[letter] > 0) {
        result.push(String.fromCharCode(97 + letter));
        counts[letter]--;
      }
    }
  }
  return result.join('');
}

const sortString = solve;
class Solution {
  sortString(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sortString };
