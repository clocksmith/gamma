"use strict";

function solve(grid, health) {
  const m = grid.length, n = grid[0].length;
  const INF = 1e9;
  const dist = new Int32Array(m * n).fill(INF);
  dist[0] = grid[0][0];
  const cap = m * n * 2 + 5;
  const q = new Int32Array(cap * 2);
  let head = cap, tail = cap;
  q[tail++] = 0;
  const dr = [-1, 1, 0, 0];
  const dc = [0, 0, -1, 1];
  while (head < tail) {
    const u = q[head++];
    const r = Math.floor(u / n), c = u % n;
    const d = dist[u];
    for (let k = 0; k < 4; k++) {
      const nr = r + dr[k], nc = c + dc[k];
      if (nr >= 0 && nr < m && nc >= 0 && nc < n) {
        const v = nr * n + nc;
        const w = grid[nr][nc];
        if (d + w < dist[v]) {
          dist[v] = d + w;
          if (w === 0) q[--head] = v;
          else q[tail++] = v;
        }
      }
    }
  }
  return dist[m * n - 1] < health;
}

function findSafeWalk(grid, health) {
  return solve(grid, health);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.findSafeWalk = findSafeWalk;
