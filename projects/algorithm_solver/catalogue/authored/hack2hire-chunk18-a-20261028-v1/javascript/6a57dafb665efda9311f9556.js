"use strict";
// Hack2Hire 6a57dafb665efda9311f9556 (Maximum Grid Jumping Path, variant 4 of 4) over an INFERRED spec; qualification unknown.

const MOD = 1000000007;

function solve(board, p, k) {
  const rows = board.length, cols = board[0].length;
  const value = [], count = [];
  for (let i = 0; i < rows; i++) {
    const vl = [], cl = [];
    for (let u = 0; u <= k; u++) {
      vl.push(new Array(cols).fill(null));
      cl.push(new Array(cols).fill(0));
    }
    value.push(vl);
    count.push(cl);
  }
  value[0][0][p] = board[0][p];
  count[0][0][p] = 1;
  for (let i = 1; i < rows; i++) {
    for (let u = 0; u <= k; u++) {
      const sources = [[i - 1, u, -1], [i - 1, u, 0], [i - 1, u, 1]];
      if (i >= 2 && u >= 1) sources.push([i - 2, u - 1, 0]);
      for (let j = 0; j < cols; j++) {
        let top = null, ways = 0;
        for (const [a, w, d] of sources) {
          const c = j + d;
          if (c < 0 || c >= cols) continue;
          const v = value[a][w][c];
          if (v === null) continue;
          if (top === null || v > top) {
            top = v;
            ways = count[a][w][c];
          } else if (v === top) ways = (ways + count[a][w][c]) % MOD;
        }
        if (top !== null) {
          value[i][u][j] = top + board[i][j];
          count[i][u][j] = ways;
        }
      }
    }
  }
  let top = null, ways = 0;
  for (let u = 0; u <= k; u++) {
    for (let j = 0; j < cols; j++) {
      const v = value[rows - 1][u][j];
      if (v === null) continue;
      if (top === null || v > top) {
        top = v;
        ways = count[rows - 1][u][j];
      } else if (v === top) ways = (ways + count[rows - 1][u][j]) % MOD;
    }
  }
  return ways;
}

function countBestPaths(board, p, k) { return solve(board, p, k); }

module.exports = solve;
module.exports.countBestPaths = countBestPaths;
