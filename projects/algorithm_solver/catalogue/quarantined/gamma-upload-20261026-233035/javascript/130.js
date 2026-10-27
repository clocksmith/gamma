'use strict';
// 130. Surrounded Regions.
function solve(board) {
  if (!board.length || !board[0].length) return;
  const rows = board.length;
  const columns = board[0].length;
  const queue = [];
  function add(row, column) {
    if (board[row][column] === 'O') { board[row][column] = '#'; queue.push([row, column]); }
  }
  for (let row = 0; row < rows; row += 1) { add(row, 0); add(row, columns - 1); }
  for (let column = 0; column < columns; column += 1) { add(0, column); add(rows - 1, column); }
  for (let head = 0; head < queue.length; head += 1) {
    const [row, column] = queue[head];
    for (const [dr, dc] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      const nr = row + dr; const nc = column + dc;
      if (nr >= 0 && nr < rows && nc >= 0 && nc < columns && board[nr][nc] === 'O') add(nr, nc);
    }
  }
  for (let row = 0; row < rows; row += 1) for (let column = 0; column < columns; column += 1) {
    board[row][column] = board[row][column] === '#' ? 'O' : 'X';
  }
}
class Solution { solve(board) { solve(board); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution };
