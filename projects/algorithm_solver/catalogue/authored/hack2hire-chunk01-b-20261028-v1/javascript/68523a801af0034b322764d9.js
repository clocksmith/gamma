"use strict";
// Hack2Hire 68523a801af0034b322764d9 (Find Optimal Commute, variant 1: single mode). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown.

function solve(grid, modes, times, costs) {
  const rows = grid.length, cols = grid[0].length;
  let start = -1;
  for (let r = 0; r < rows && start < 0; r++) {
    const c = grid[r].indexOf("S");
    if (c >= 0) start = r * cols + c;
  }
  const moves = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  let best = null;
  for (let m = 0; m < modes.length; m++) {
    const digit = String(m + 1), steps = new Array(rows * cols).fill(-1), frontier = [start];
    steps[start] = 0;
    let found = -1;
    for (let head = 0; head < frontier.length && found < 0; head++) {
      const cell = frontier[head], r = Math.floor(cell / cols), c = cell % cols;
      for (const [dr, dc] of moves) {
        const x = r + dr, y = c + dc;
        if (x < 0 || x >= rows || y < 0 || y >= cols || steps[x * cols + y] >= 0) continue;
        const ch = grid[x][y];
        if (ch === "D") {
          found = steps[cell] + 1;
          break;
        }
        if (ch === digit) {
          steps[x * cols + y] = steps[cell] + 1;
          frontier.push(x * cols + y);
        }
      }
    }
    if (found >= 0) {
      const charged = found - 1, key = [charged * times[m], charged * costs[m], m];
      if (best === null || key[0] < best[0] || (key[0] === best[0] && key[1] < best[1])) best = key;
    }
  }
  return best === null ? "" : modes[best[2]];
}

function optimalCommuteMode(grid, modes, times, costs) { return solve(grid, modes, times, costs); }
module.exports = solve;
module.exports.optimalCommuteMode = optimalCommuteMode;
