'use strict';

// 289. Game of Life (Medium).
// Specification: https://leetcode.com/problems/game-of-life/description/
function solve(board) {
  const rows = board.length; const cols = board[0].length;
  const next = board.map((row) => row.slice());
  const directions = [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      let live = 0;
      for (const [dr, dc] of directions) {
        const nr = r + dr; const nc = c + dc;
        if (nr >= 0 && nr < rows && nc >= 0 && nc < cols) live += board[nr][nc];
      }
      if (board[r][c] === 1) next[r][c] = (live === 2 || live === 3) ? 1 : 0;
      else next[r][c] = live === 3 ? 1 : 0;
    }
  }
  return next;
}
const gameOfLife = solve;
class Solution { gameOfLife(board) { return solve(board); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, gameOfLife };
