"use strict";
// Hack2Hire 68dc5856dd5418be11109afb (Shortest Path with Gas Stations) over an INFERRED spec; qualification unknown.

function solve(grid, fuelCapacity) {
  const m = grid.length, n = grid[0].length;
  let sr = 0, sc = 0;
  grid.forEach((row, r) => { const c = row.indexOf("S"); if (c >= 0) { sr = r; sc = c; } });
  const best = Array.from({length: m}, () => new Array(n).fill(-1));
  best[sr][sc] = fuelCapacity;
  let frontier = [[sr, sc, fuelCapacity]], steps = 0;
  while (frontier.length) {
    const following = [];
    for (const [r, c, fuel] of frontier) {
      if (grid[r][c] === "D") return steps;
      if (fuel === 0) continue;
      for (const [rr, cc] of [[r + 1, c], [r - 1, c], [r, c + 1], [r, c - 1]]) {
        if (rr >= 0 && rr < m && cc >= 0 && cc < n && grid[rr][cc] !== "#") {
          const left = grid[rr][cc] === "G" ? fuelCapacity : fuel - 1;
          if (left > best[rr][cc]) { best[rr][cc] = left; following.push([rr, cc, left]); }
        }
      }
    }
    frontier = following;
    steps++;
  }
  return -1;
}

function shortestPathWithFuel(grid, fuelCapacity) { return solve(grid, fuelCapacity); }

module.exports = solve;
module.exports.shortestPathWithFuel = shortestPathWithFuel;
