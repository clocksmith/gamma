'use strict';

// 1812. Determine Color of a Chessboard Square (Easy).
// Specification: https://leetcode.com/problems/determine-color-of-a-chessboard-square/description/
// O(1) time and space; coordinates range from a1 through h8.
function solve(coordinates) {
  const column = coordinates.charCodeAt(0) - 97;
  const row = coordinates.charCodeAt(1) - 49;
  return (column + row) % 2 === 1;
}

const squareIsWhite = solve;
class Solution {
  squareIsWhite(coordinates) { return solve(coordinates); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, squareIsWhite };
