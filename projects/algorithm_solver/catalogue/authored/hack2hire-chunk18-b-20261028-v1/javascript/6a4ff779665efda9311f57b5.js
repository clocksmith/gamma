"use strict";
// Hack2Hire 6a4ff779665efda9311f57b5 (Cellular Infection Spreading, variant 5 of 5) over an INFERRED spec; qualification unknown.

function infectionDays_(grid, threshold) {
  // multi-source breadth-first search by days with a counter of infected neighbours per healthy plant
  const m = grid.length, n = grid[0].length;
  const day = grid.map((row) => row.map((v) => (v ? 0 : -1)));
  const count = [];
  for (let i = 0; i < m; i++) count.push(new Array(n).fill(0));
  let frontier = [];
  for (let i = 0; i < m; i++) for (let j = 0; j < n; j++) if (grid[i][j]) frontier.push(i * n + j);
  let current = 0, last = 0;
  while (frontier.length) {
    const following = [];
    for (const cell of frontier) {
      const i = Math.floor(cell / n), j = cell - i * n;
      const aEnd = Math.min(m, i + 2), bEnd = Math.min(n, j + 2);
      for (let a = Math.max(0, i - 1); a < aEnd; a++) {
        const dayRow = day[a], countRow = count[a];
        for (let b = Math.max(0, j - 1); b < bEnd; b++) {
          if (dayRow[b] === -1) {
            countRow[b] += 1;
            if (countRow[b] === threshold) following.push(a * n + b);
          }
        }
      }
    }
    current += 1;
    for (const cell of following) { const a = Math.floor(cell / n); day[a][cell - a * n] = current; }
    if (following.length) last = current;
    frontier = following;
  }
  return [day, last];
}

function solve(grid, threshold) {
  return infectionDays_(grid, threshold)[0];
}

function infectionDays(grid, threshold) { return solve(grid, threshold); }

module.exports = solve;
module.exports.infectionDays = infectionDays;
