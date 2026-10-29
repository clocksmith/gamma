"use strict";

function dist1d(arr) {
  let l = 0, r = arr.length - 1, s = 0;
  while (l < r) s += arr[r--] - arr[l++];
  return s;
}

function solve(grid) {
  const m = grid.length, n = grid[0].length;
  const rows = [];
  const cols = [];
  for (let r = 0; r < m; r++) {
    for (let c = 0; c < n; c++) {
      if (grid[r][c] === 1) rows.push(r);
    }
  }
  for (let c = 0; c < n; c++) {
    for (let r = 0; r < m; r++) {
      if (grid[r][c] === 1) cols.push(c);
    }
  }
  return dist1d(rows) + dist1d(cols);
}

function minTotalDistance(grid) {
  return solve(grid);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.minTotalDistance = minTotalDistance;
