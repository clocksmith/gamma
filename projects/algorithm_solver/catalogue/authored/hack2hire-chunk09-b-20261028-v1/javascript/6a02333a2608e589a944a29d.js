"use strict";
// Hack2Hire 6a02333a2608e589a944a29d (Calculate Board Score) over an INFERRED spec; qualification unknown.

function solve(board) {
  const rows = board.length, cols = board[0].length, size = rows * cols;
  const seen = new Uint8Array(size), queue = new Int32Array(size);
  let total = 0;
  for (let start = 0; start < size; start++) {
    if (seen[start]) continue;
    const terrain = board[(start / cols) | 0][start % cols][0];
    seen[start] = 1;
    let head = 0, tail = 0, crowns = 0;
    queue[tail++] = start;
    while (head < tail) {
      const cell = queue[head++], r = (cell / cols) | 0, c = cell - r * cols;
      crowns += board[r][c].charCodeAt(1) - 48;
      if (r > 0 && !seen[cell - cols] && board[r - 1][c][0] === terrain) { seen[cell - cols] = 1; queue[tail++] = cell - cols; }
      if (r + 1 < rows && !seen[cell + cols] && board[r + 1][c][0] === terrain) { seen[cell + cols] = 1; queue[tail++] = cell + cols; }
      if (c > 0 && !seen[cell - 1] && board[r][c - 1][0] === terrain) { seen[cell - 1] = 1; queue[tail++] = cell - 1; }
      if (c + 1 < cols && !seen[cell + 1] && board[r][c + 1][0] === terrain) { seen[cell + 1] = 1; queue[tail++] = cell + 1; }
    }
    total += tail * crowns;
  }
  return total;
}

function calculateScore(board) { return solve(board); }

module.exports = solve;
module.exports.calculateScore = calculateScore;
