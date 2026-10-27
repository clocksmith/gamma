'use strict';

// 500. Keyboard Row.

function solve(words) {
  const row = new Map();
  ['qwertyuiop', 'asdfghjkl', 'zxcvbnm'].forEach((letters, index) => {
    for (const char of letters) row.set(char, index);
  });
  return words.filter(word => new Set(Array.from(word.toLowerCase(), char => row.get(char))).size <= 1);
}

const findWords = solve;
class Solution {
  findWords(words) { return solve(words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findWords };
