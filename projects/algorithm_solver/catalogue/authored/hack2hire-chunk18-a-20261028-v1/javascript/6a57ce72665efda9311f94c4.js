"use strict";
// Hack2Hire 6a57ce72665efda9311f94c4 (Maximum Grid Jumping Path, variant 1 of 4) over an INFERRED spec; qualification unknown.

function solve(board, p) {
  const rows = board.length, cols = board[0].length;
  let current = new Array(cols).fill(null);
  current[p] = board[0][p];
  for (let i = 1; i < rows; i++) {
    const next = new Array(cols).fill(null);
    const row = board[i];
    for (let j = 0; j < cols; j++) {
      let best = null;
      for (let c = j - 1; c <= j + 1; c++) {
        if (c >= 0 && c < cols && current[c] !== null && (best === null || current[c] > best)) best = current[c];
      }
      if (best !== null) next[j] = best + row[j];
    }
    current = next;
  }
  let answer = null;
  for (const v of current) if (v !== null && (answer === null || v > answer)) answer = v;
  return answer;
}

function maxPathScore(board, p) { return solve(board, p); }

module.exports = solve;
module.exports.maxPathScore = maxPathScore;
