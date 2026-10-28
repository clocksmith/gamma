'use strict';

// 419. Battleships in a Board (Medium).
// Specification: https://leetcode.com/problems/battleships-in-a-board/description/
function solve(board) {
  let count = 0;
  for (let r = 0; r < board.length; r++) {
    for (let c = 0; c < board[0].length; c++) {
      if (board[r][c] !== 'X') continue;
      if (r > 0 && board[r - 1][c] === 'X') continue;
      if (c > 0 && board[r][c - 1] === 'X') continue;
      count++;
    }
  }
  return count;
}
const countBattleships = solve;
class Solution { countBattleships(board) { return solve(board); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, countBattleships };
