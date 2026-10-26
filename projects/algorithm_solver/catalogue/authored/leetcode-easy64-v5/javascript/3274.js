'use strict';

// 3274. Check if Two Chessboard Squares Have the Same Color (Easy).
// Specification: https://leetcode.com/problems/check-if-two-chessboard-squares-have-the-same-color/description/
// O(1) time and space; both coordinates are valid two-character chessboard squares.
function solve(coordinate1, coordinate2) {
  const first = coordinate1.charCodeAt(0) + coordinate1.charCodeAt(1);
  const second = coordinate2.charCodeAt(0) + coordinate2.charCodeAt(1);
  return first % 2 === second % 2;
}

const checkTwoChessboards = solve;
class Solution {
  checkTwoChessboards(coordinate1, coordinate2) { return solve(coordinate1, coordinate2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkTwoChessboards };
