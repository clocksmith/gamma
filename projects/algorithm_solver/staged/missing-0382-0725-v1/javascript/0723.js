'use strict';

// 723. Candy Crush. Mark simultaneous matches, apply gravity, and repeat; intentionally mutate and return the supplied board.

function solve(board) {
  const rows = board.length, cols = board[0].length;
  while (true) {
    const remove = new Set();
    for (let r = 0; r < rows; r += 1) for (let c = 0; c + 2 < cols; c += 1) {
      if (board[r][c] && board[r][c] === board[r][c + 1] && board[r][c] === board[r][c + 2]) {
        remove.add(r * cols + c); remove.add(r * cols + c + 1); remove.add(r * cols + c + 2);
      }
    }
    for (let r = 0; r + 2 < rows; r += 1) for (let c = 0; c < cols; c += 1) {
      if (board[r][c] && board[r][c] === board[r + 1][c] && board[r][c] === board[r + 2][c]) {
        remove.add(r * cols + c); remove.add((r + 1) * cols + c); remove.add((r + 2) * cols + c);
      }
    }
    if (remove.size === 0) return board;
    for (const cell of remove) board[Math.floor(cell / cols)][cell % cols] = 0;
    for (let c = 0; c < cols; c += 1) {
      let write = rows - 1;
      for (let r = rows - 1; r >= 0; r -= 1) if (board[r][c]) board[write--][c] = board[r][c];
      while (write >= 0) board[write--][c] = 0;
    }
  }
}

const candyCrush = solve;
class Solution {
  candyCrush(board) { return solve(board); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, candyCrush };
