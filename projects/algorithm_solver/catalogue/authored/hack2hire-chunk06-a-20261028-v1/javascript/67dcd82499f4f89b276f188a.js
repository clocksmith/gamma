"use strict";
// Hack2Hire 67dcd82499f4f89b276f188a (Find Shortest Path in Matrix) over an INFERRED spec; qualification unknown.

function solve(grid) {
  const m = grid.length, n = grid[0].length;
  if (grid[0][0] === 0 || grid[m - 1][n - 1] === 0) return -1;
  const target = m * n - 1, distance = new Int32Array(m * n).fill(-1), queue = new Int32Array(m * n);
  distance[0] = 0;
  let head = 0, tail = 1;
  while (head < tail) {
    const v = queue[head++];
    if (v === target) return distance[v] + 1;
    const c = v % n, r = (v - c) / n;
    for (let dr = -1; dr <= 1; dr++) {
      const rr = r + dr;
      if (rr < 0 || rr >= m) continue;
      const row = grid[rr];
      for (let dc = -1; dc <= 1; dc++) {
        const cc = c + dc;
        if (cc >= 0 && cc < n && row[cc] !== 0) {
          const w = rr * n + cc;
          if (distance[w] < 0) { distance[w] = distance[v] + 1; queue[tail++] = w; }
        }
      }
    }
  }
  return -1;
}

function shortestPath(grid) { return solve(grid); }

module.exports = solve;
module.exports.shortestPath = shortestPath;
