"use strict";
// Hack2Hire 680d8976286d3dbf97693ad5 (Four-in-a-row Game) over an INFERRED spec; qualification unknown.

function solve(board, move, player) {
  const [x, y] = move;
  const rows = board.length, cols = board[0].length;
  for (const [dx, dy] of [[0, 1], [1, 0], [1, 1], [1, -1]]) {
    let run = 1;
    for (const sign of [1, -1]) {
      let a = x + sign * dx, b = y + sign * dy, steps = 0;
      while (steps < 3 && a >= 0 && a < rows && b >= 0 && b < cols && board[a][b] === player) {
        run++;
        steps++;
        a += sign * dx;
        b += sign * dy;
      }
    }
    if (run >= 4) return true;
  }
  return false;
}

function isWinningMove(board, move, player) { return solve(board, move, player); }

module.exports = solve;
module.exports.isWinningMove = isWinningMove;
