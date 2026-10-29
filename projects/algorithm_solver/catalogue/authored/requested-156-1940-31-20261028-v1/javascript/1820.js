"use strict";

function solve(grid) {
  const m = grid.length, n = grid[0].length;
  const match = new Int32Array(n).fill(-1);
  function dfs(u, vis) {
    for (let v = 0; v < n; v++) {
      if (grid[u][v] && !vis[v]) {
        vis[v] = 1;
        if (match[v] === -1 || dfs(match[v], vis)) {
          match[v] = u;
          return true;
        }
      }
    }
    return false;
  }
  let ans = 0;
  for (let u = 0; u < m; u++) {
    if (dfs(u, new Uint8Array(n))) ans++;
  }
  return ans;
}

function maximumInvitations(grid) {
  return solve(grid);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.maximumInvitations = maximumInvitations;
