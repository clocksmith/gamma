"use strict";
// Hack2Hire 67a93084ea201244f8fae263 (Minimum Flips for Grid Symmetry) over an INFERRED spec; qualification unknown.

function solve(grid) {
  const n = grid.length, m = grid[0].length;
  let flips = 0;
  for (let i = 0; i < (n + 1) >> 1; i++) {
    const rows = i === n - 1 - i ? [i] : [i, n - 1 - i];
    for (let j = 0; j < (m + 1) >> 1; j++) {
      const cols = j === m - 1 - j ? [j] : [j, m - 1 - j];
      let black = 0;
      for (const r of rows) for (const c of cols) if (grid[r][c] === "B") black++;
      const size = rows.length * cols.length;
      flips += Math.min(black, size - black);
    }
  }
  return flips;
}

function minFlips(grid) { return solve(grid); }

module.exports = solve;
module.exports.minFlips = minFlips;
