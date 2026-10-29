"use strict";
// Hack2Hire 6789faf811318cc872dd83f3 (Find Robots Position). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown.

function solve(board, distances) {
  const rows = board.length, cols = board[0].length, area = rows * cols;
  const left = new Array(area).fill(0), right = new Array(area).fill(0);
  const top = new Array(area).fill(0), bottom = new Array(area).fill(0);
  for (let r = 0; r < rows; r++) {
    let blocker = -1;
    for (let c = 0; c < cols; c++) {
      if (board[r][c] === "X") blocker = c;
      else left[r * cols + c] = c - blocker;
    }
    blocker = cols;
    for (let c = cols - 1; c >= 0; c--) {
      if (board[r][c] === "X") blocker = c;
      else right[r * cols + c] = blocker - c;
    }
  }
  for (let c = 0; c < cols; c++) {
    let blocker = -1;
    for (let r = 0; r < rows; r++) {
      if (board[r][c] === "X") blocker = r;
      else top[r * cols + c] = r - blocker;
    }
    blocker = rows;
    for (let r = rows - 1; r >= 0; r--) {
      if (board[r][c] === "X") blocker = r;
      else bottom[r * cols + c] = blocker - r;
    }
  }
  const [wantLeft, wantTop, wantBottom, wantRight] = distances, out = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const i = r * cols + c;
      if (board[r][c] === "O" && left[i] === wantLeft && top[i] === wantTop && bottom[i] === wantBottom && right[i] === wantRight) out.push([r, c]);
    }
  }
  return out;
}

function findRobotPositions(board, distances) { return solve(board, distances); }
module.exports = solve;
module.exports.findRobotPositions = findRobotPositions;
