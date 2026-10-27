'use strict';

// 419. Battleships in a Board. Count each valid ship at its top-left endpoint; do not modify the board.

function solve(board) {
  let count = 0;
  for (let r = 0; r < board.length; r += 1) {
    for (let c = 0; c < board[0].length; c += 1) {
      if (board[r][c] === 'X' && (r === 0 || board[r - 1][c] !== 'X') && (c === 0 || board[r][c - 1] !== 'X')) count += 1;
    }
  }
  return count;
}

const countBattleships = solve;
class Solution {
  countBattleships(board) { return solve(board); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countBattleships };
