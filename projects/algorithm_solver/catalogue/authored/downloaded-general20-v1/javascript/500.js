'use strict';

// 500. Keyboard Row (Easy).
// Specification: https://leetcode.com/problems/keyboard-row/description/
const ROWS = ["qwertyuiop", "asdfghjkl", "zxcvbnm"];

function solve(words) {
  const answer = [];
  for (const word of words) {
    const lower = word.toLowerCase();
    const row = ROWS.find((candidate) => candidate.includes(lower[0]));
    if (row && [...lower].every((ch) => row.includes(ch))) answer.push(word);
  }
  return answer;
}

const findWords = solve;
class Solution {
  findWords(words) { return solve(words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findWords };
