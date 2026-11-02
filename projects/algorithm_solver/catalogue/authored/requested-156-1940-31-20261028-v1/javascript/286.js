"use strict";

function solve(rooms) {
  const INF = 2147483647;
  const m = rooms.length, n = rooms[0].length;
  const grid = rooms.map((row) => row.slice());
  const q = [];
  for (let r = 0; r < m; r++) {
    for (let c = 0; c < n; c++) {
      if (grid[r][c] === 0) q.push([r, c]);
    }
  }
  const dr = [-1, 1, 0, 0], dc = [0, 0, -1, 1];
  for (let i = 0; i < q.length; i++) {
    const [r, c] = q[i];
    for (let k = 0; k < 4; k++) {
      const nr = r + dr[k], nc = c + dc[k];
      if (nr >= 0 && nr < m && nc >= 0 && nc < n && grid[nr][nc] === INF) {
        grid[nr][nc] = grid[r][c] + 1;
        q.push([nr, nc]);
      }
    }
  }
  return grid;
}

// Official LeetCode ABI (in_place_arg 0): rewrites rooms in place row by row
// and returns nothing. The intermediate grid from solve is charged as
// O(m * n) auxiliary space; the write-back as O(m * n) time.
function wallsAndGates(rooms) {
  const out = solve(rooms);
  for (let r = 0; r < out.length; r++) {
    const row = rooms[r];
    for (let c = 0; c < out[r].length; c++) row[c] = out[r][c];
  }
}

module.exports = solve;
module.exports.solve = solve;
module.exports.wallsAndGates = wallsAndGates;
if (typeof Solution !== "undefined") solve.Solution = Solution;
