'use strict';

// 36. Valid Sudoku (Medium).
// Specification: https://leetcode.com/problems/valid-sudoku/description/
function solve(board) {
  const seen = new Set();
  for (let r = 0; r < 9; r++) {
    for (let c = 0; c < 9; c++) {
      const value = board[r][c];
      if (value === '.') continue;
      const rowKey = `r${r}-${value}`; const colKey = `c${c}-${value}`; const boxKey = `b${Math.floor(r / 3)}-${Math.floor(c / 3)}-${value}`;
      if (seen.has(rowKey) || seen.has(colKey) || seen.has(boxKey)) return false;
      seen.add(rowKey); seen.add(colKey); seen.add(boxKey);
    }
  }
  return true;
}
const isValidSudoku = solve;
class Solution { isValidSudoku(board) { return solve(board); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, isValidSudoku };
