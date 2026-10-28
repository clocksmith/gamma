'use strict';

// 794. Valid Tic-Tac-Toe State (Medium).
// Specification: https://leetcode.com/problems/valid-tic-tac-toe-state/description/
function wins(board, player) {
  for (let i = 0; i < 3; i++) {
    if (board[i][0] === player && board[i][1] === player && board[i][2] === player) return true;
    if (board[0][i] === player && board[1][i] === player && board[2][i] === player) return true;
  }
  if (board[0][0] === player && board[1][1] === player && board[2][2] === player) return true;
  if (board[0][2] === player && board[1][1] === player && board[2][0] === player) return true;
  return false;
}
function solve(board) {
  let xCount = 0; let oCount = 0;
  for (const row of board) { for (const ch of row) { if (ch === 'X') xCount++; else if (ch === 'O') oCount++; } }
  if (oCount > xCount || xCount - oCount > 1) return false;
  const xWins = wins(board, 'X');
  const oWins = wins(board, 'O');
  if (xWins && oWins) return false;
  if (xWins && xCount !== oCount + 1) return false;
  if (oWins && xCount !== oCount) return false;
  return true;
}
const validTicTacToe = solve;
class Solution { validTicTacToe(board) { return solve(board); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, validTicTacToe };
