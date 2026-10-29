"use strict";
// Hack2Hire 68e86c2f80f69c7a01706886 (Word Search in a Straight Line) over an INFERRED spec; qualification unknown.

function solve(board, word) {
  const m = board.length, n = board[0].length, length = word.length;
  const directions = [[0, 1], [0, -1], [1, 0], [-1, 0], [1, 1], [1, -1], [-1, 1], [-1, -1]];
  for (let r = 0; r < m; r++) {
    for (let c = 0; c < n; c++) {
      if (board[r][c] !== word[0]) continue;
      for (const [dr, dc] of directions) {
        const er = r + dr * (length - 1), ec = c + dc * (length - 1);
        if (er < 0 || er >= m || ec < 0 || ec >= n) continue;
        let k = 1;
        while (k < length && board[r + dr * k][c + dc * k] === word[k]) k++;
        if (k === length) return true;
      }
    }
  }
  return false;
}

function existsInStraightLine(board, word) { return solve(board, word); }

module.exports = solve;
module.exports.existsInStraightLine = existsInStraightLine;
