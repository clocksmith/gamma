'use strict';

// 422. Valid Word Square (Easy).
// Specification: https://leetcode.com/problems/valid-word-square/description/
// O(total characters) time, O(1) auxiliary space; check ragged transpose bounds; preserve words.
function solve(words) {
  for (let row = 0; row < words.length; row++) {
    for (let column = 0; column < words[row].length; column++) {
      if (column >= words.length || row >= words[column].length) return false;
      if (words[row][column] !== words[column][row]) return false;
    }
  }
  return true;
}

const validWordSquare = solve;
class Solution {
  validWordSquare(words) { return solve(words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, validWordSquare };
