'use strict';

// 804. Unique Morse Code Words (Easy).
// Specification: https://leetcode.com/problems/unique-morse-code-words/description/
// O(s) expected time and O(s) space, where s is total input length; preserve the word list.
function solve(words) {
  const codes = [
    '.-', '-...', '-.-.', '-..', '.', '..-.', '--.', '....', '..', '.---',
    '-.-', '.-..', '--', '-.', '---', '.--.', '--.-', '.-.', '...', '-',
    '..-', '...-', '.--', '-..-', '-.--', '--..'
  ];
  const representations = new Set();
  for (const word of words) {
    const parts = [];
    for (const letter of word) parts.push(codes[letter.charCodeAt(0) - 97]);
    representations.add(parts.join(''));
  }
  return representations.size;
}

const uniqueMorseRepresentations = solve;
class Solution {
  uniqueMorseRepresentations(words) { return solve(words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, uniqueMorseRepresentations };
