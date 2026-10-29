"use strict";
// Hack2Hire 6a57d29e665efda9311f950a (Maximum Grid Jumping Path, variant 2 of 4) over an INFERRED spec; qualification unknown.

function solve(board, p, k) {
  const rows = board.length, cols = board[0].length;
  // best[i][u][j]: largest sum reaching (i, j) with exactly u jumps; null when unreachable
  const best = [];
  for (let i = 0; i < rows; i++) {
    const layer = [];
    for (let u = 0; u <= k; u++) layer.push(new Array(cols).fill(null));
    best.push(layer);
  }
  best[0][0][p] = board[0][p];
  for (let i = 1; i < rows; i++) {
    const row = board[i];
    for (let u = 0; u <= k; u++) {
      const above = best[i - 1][u];
      const jump = i >= 2 && u >= 1 ? best[i - 2][u - 1] : null;
      const target = best[i][u];
      for (let j = 0; j < cols; j++) {
        let top = null;
        for (let c = j - 1; c <= j + 1; c++) {
          if (c >= 0 && c < cols && above[c] !== null && (top === null || above[c] > top)) top = above[c];
        }
        if (jump !== null && jump[j] !== null && (top === null || jump[j] > top)) top = jump[j];
        if (top !== null) target[j] = top + row[j];
      }
    }
  }
  let answer = null;
  for (const layer of best[rows - 1]) for (const v of layer) if (v !== null && (answer === null || v > answer)) answer = v;
  return answer;
}

function maxPathScoreWithJumps(board, p, k) { return solve(board, p, k); }

module.exports = solve;
module.exports.maxPathScoreWithJumps = maxPathScoreWithJumps;
