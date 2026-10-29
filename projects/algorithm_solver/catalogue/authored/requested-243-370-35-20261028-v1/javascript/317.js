"use strict";

function solve(grid) {
  const m = grid.length, n = grid[0].length;
  const totalDist = Array.from({ length: m }, () => new Int32Array(n));
  const reach = Array.from({ length: m }, () => new Int32Array(n));
  let buildings = 0;
  const dr = [-1, 1, 0, 0], dc = [0, 0, -1, 1];
  for (let r = 0; r < m; r++) {
    for (let c = 0; c < n; c++) {
      if (grid[r][c] === 1) {
        buildings++;
        const vis = Array.from({ length: m }, () => new Uint8Array(n));
        vis[r][c] = 1;
        const q = [[r, c, 0]];
        for (let i = 0; i < q.length; i++) {
          const [cr, cc, d] = q[i];
          for (let k = 0; k < 4; k++) {
            const nr = cr + dr[k], nc = cc + dc[k];
            if (nr >= 0 && nr < m && nc >= 0 && nc < n && !vis[nr][nc] && grid[nr][nc] === 0) {
              vis[nr][nc] = 1;
              totalDist[nr][nc] += d + 1;
              reach[nr][nc] += 1;
              q.push([nr, nc, d + 1]);
            }
          }
        }
      }
    }
  }
  let ans = 1e15;
  for (let r = 0; r < m; r++) {
    for (let c = 0; c < n; c++) {
      if (grid[r][c] === 0 && reach[r][c] === buildings && totalDist[r][c] < ans) {
        ans = totalDist[r][c];
      }
    }
  }
  return ans === 1e15 ? -1 : ans;
}

function shortestDistance(grid) {
  return solve(grid);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.shortestDistance = shortestDistance;
