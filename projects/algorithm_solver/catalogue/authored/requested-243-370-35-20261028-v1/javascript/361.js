"use strict";

function solve(grid) {
  const m = grid.length, n = grid[0].length;
  let rowHits = 0;
  const colHits = new Int32Array(n);
  let best = 0;
  for (let r = 0; r < m; r++) {
    for (let c = 0; c < n; c++) {
      if (c === 0 || grid[r][c - 1] === "W") {
        rowHits = 0;
        for (let k = c; k < n && grid[r][k] !== "W"; k++) {
          if (grid[r][k] === "E") rowHits++;
        }
      }
      if (r === 0 || grid[r - 1][c] === "W") {
        colHits[c] = 0;
        for (let k = r; k < m && grid[k][c] !== "W"; k++) {
          if (grid[k][c] === "E") colHits[c]++;
        }
      }
      if (grid[r][c] === "0") {
        if (rowHits + colHits[c] > best) best = rowHits + colHits[c];
      }
    }
  }
  return best;
}

function maxKilledEnemies(grid) {
  return solve(grid);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.maxKilledEnemies = maxKilledEnemies;
