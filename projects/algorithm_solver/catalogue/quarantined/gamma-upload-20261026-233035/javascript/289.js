'use strict';
// 289. Game of Life.
function solve(board) {
  const rows = board.length; const columns = board[0].length;
  for (let row = 0; row < rows; row += 1) for (let column = 0; column < columns; column += 1) {
    let live = 0;
    for (let dr = -1; dr <= 1; dr += 1) for (let dc = -1; dc <= 1; dc += 1) if (dr !== 0 || dc !== 0) {
      const nr = row + dr; const nc = column + dc;
      if (nr >= 0 && nr < rows && nc >= 0 && nc < columns) live += board[nr][nc] & 1;
    }
    if (((board[row][column] & 1) && (live === 2 || live === 3)) || (!(board[row][column] & 1) && live === 3)) {
      board[row][column] |= 2;
    }
  }
  for (let row = 0; row < rows; row += 1) for (let column = 0; column < columns; column += 1) board[row][column] >>= 1;
}
const gameOfLife = solve;
class Solution { gameOfLife(board) { solve(board); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, gameOfLife };
