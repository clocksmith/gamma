"use strict";
// Hack2Hire 6a57d9ca665efda9311f954c (Maximum Grid Jumping Path, variant 3 of 4) over an INFERRED spec; qualification unknown.

function solve(board, p, k) {
  const rows = board.length, cols = board[0].length;
  // down[i][r][j]: best sum from (i, j), counting it, to the bottom row with at most r jumps left
  const down = new Array(rows);
  down[rows - 1] = [];
  for (let r = 0; r <= k; r++) down[rows - 1].push(board[rows - 1].slice());
  for (let i = rows - 2; i >= 0; i--) {
    const row = board[i];
    const layer = [];
    for (let r = 0; r <= k; r++) {
      const below = down[i + 1][r];
      const far = r >= 1 && i + 2 <= rows - 1 ? down[i + 2][r - 1] : null;
      const values = new Array(cols);
      for (let j = 0; j < cols; j++) {
        let top = below[j];
        if (j > 0 && below[j - 1] > top) top = below[j - 1];
        if (j + 1 < cols && below[j + 1] > top) top = below[j + 1];
        if (far !== null && far[j] > top) top = far[j];
        values[j] = top + row[j];
      }
      layer.push(values);
    }
    down[i] = layer;
  }
  const path = [[0, p]];
  let i = 0, j = p, r = k;
  while (i < rows - 1) {
    const need = down[i][r][j] - board[i][j];
    const moves = [[i + 1, j - 1, r], [i + 1, j, r], [i + 1, j + 1, r]];
    if (r >= 1 && i + 2 <= rows - 1) moves.push([i + 2, j, r - 1]);
    for (const [a, b, left] of moves) {
      if (b >= 0 && b < cols && down[a][left][b] === need) {
        i = a;
        j = b;
        r = left;
        break;
      }
    }
    path.push([i, j]);
  }
  return path;
}

function bestPathWithJumps(board, p, k) { return solve(board, p, k); }

module.exports = solve;
module.exports.bestPathWithJumps = bestPathWithJumps;
