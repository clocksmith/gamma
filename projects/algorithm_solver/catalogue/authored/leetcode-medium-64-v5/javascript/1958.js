'use strict';

// 1958. Check if Move is Legal: look for an opposite-color run closed by the chosen color in any direction.
// O(1) time and O(1) auxiliary space on the fixed 8-by-8 board; inputs are read-only.
function solve(board, rMove, cMove, color) {
  const opponent = color === 'B' ? 'W' : 'B';
  for (let dr = -1; dr <= 1; dr += 1) {
    for (let dc = -1; dc <= 1; dc += 1) {
      if (dr === 0 && dc === 0) continue;
      let row = rMove + dr;
      let column = cMove + dc;
      let crossed = 0;
      while (row >= 0 && row < 8 && column >= 0 && column < 8 && board[row][column] === opponent) {
        crossed += 1;
        row += dr;
        column += dc;
      }
      if (crossed > 0 && row >= 0 && row < 8 && column >= 0 && column < 8 && board[row][column] === color) {
        return true;
      }
    }
  }
  return false;
}

const checkMove = solve;
class Solution {
  checkMove(board, rMove, cMove, color) { return solve(board, rMove, cMove, color); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkMove };
