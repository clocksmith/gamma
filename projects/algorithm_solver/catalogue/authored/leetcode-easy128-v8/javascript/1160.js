'use strict';

// 1160. Find Words That Can Be Formed by Characters (Easy).
// Specification: https://leetcode.com/problems/find-words-that-can-be-formed-by-characters/description/
// O(total characters) time, O(1) alphabet space; reset letter usage for each word.
function solve(words, chars) {
  const available = new Array(26).fill(0);
  for (const character of chars) available[character.charCodeAt(0) - 97]++;
  let total = 0;
  for (const word of words) {
    const used = new Array(26).fill(0);
    let valid = true;
    for (const character of word) {
      const letter = character.charCodeAt(0) - 97;
      used[letter]++;
      if (used[letter] > available[letter]) {
        valid = false;
        break;
      }
    }
    if (valid) total += word.length;
  }
  return total;
}

const countCharacters = solve;
class Solution {
  countCharacters(words, chars) { return solve(words, chars); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countCharacters };
