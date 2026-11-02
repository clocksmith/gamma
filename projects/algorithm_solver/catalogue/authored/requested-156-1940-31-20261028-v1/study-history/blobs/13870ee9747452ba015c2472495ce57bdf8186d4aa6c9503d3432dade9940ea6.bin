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

function wallsAndGates(rooms) {
  return solve(rooms);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.wallsAndGates = wallsAndGates;
