'use strict';

// 1897. Redistribute Characters to Make All Strings Equal (Easy).
// Specification: https://leetcode.com/problems/redistribute-characters-to-make-all-strings-equal/description/
// O(total characters) time, O(1) space for the lowercase ASCII alphabet.
function solve(words) {
  const counts = new Array(26).fill(0);
  for (const word of words) {
    for (const character of word) counts[character.charCodeAt(0) - 97]++;
  }
  for (const count of counts) {
    if (count % words.length !== 0) return false;
  }
  return true;
}

const makeEqual = solve;
class Solution {
  makeEqual(words) { return solve(words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, makeEqual };
