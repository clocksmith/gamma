'use strict';

// 130. Surrounded Regions (Medium).
// Specification: https://leetcode.com/problems/surrounded-regions/description/
function solve(board) {
  const rows = board.length; const cols = board[0].length;
  const result = board.map((row) => row.slice());
  function mark(r, c) {
    if (r < 0 || r >= rows || c < 0 || c >= cols || result[r][c] !== 'O') return;
    result[r][c] = 'S';
    mark(r + 1, c); mark(r - 1, c); mark(r, c + 1); mark(r, c - 1);
  }
  for (let r = 0; r < rows; r++) { mark(r, 0); mark(r, cols - 1); }
  for (let c = 0; c < cols; c++) { mark(0, c); mark(rows - 1, c); }
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      if (result[r][c] === 'O') result[r][c] = 'X';
      else if (result[r][c] === 'S') result[r][c] = 'O';
    }
  }
  return result;
}
const solveBoard = solve;
class Solution { solve(board) { return solve(board); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, solveBoard };
