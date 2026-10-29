"use strict";
// Original Hack2Hire 69c3477921f6ab42269655fa variant over an INFERRED specification; qualification unknown.
const DIRECTIONS = [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]];
function solve(board, row, col, player) {
  const n = board.length, out = board.map((line) => [...line]);
  if (board[row][col] !== ".") return out;
  const flips = [];
  for (const [dr, dc] of DIRECTIONS) {
    let r = row + dr, c = col + dc;
    const run = [];
    while (r >= 0 && r < n && c >= 0 && c < n && board[r][c] !== "." && board[r][c] !== player) { run.push([r, c]); r += dr; c += dc; }
    if (run.length && r >= 0 && r < n && c >= 0 && c < n && board[r][c] === player) flips.push(...run);
  }
  if (flips.length) {
    out[row][col] = player;
    for (const [r, c] of flips) out[r][c] = player;
  }
  return out;
}
function reversiMove(board, row, col, player) { return solve(board, row, col, player); }
module.exports = solve;
module.exports.reversiMove = reversiMove;
