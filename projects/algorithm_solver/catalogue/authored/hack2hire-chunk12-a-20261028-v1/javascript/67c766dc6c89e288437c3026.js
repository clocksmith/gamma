"use strict";
// Hack2Hire 67c766dc6c89e288437c3026 (Maximum Building Height) over an INFERRED spec; qualification unknown.

function solve(grid) {
  const m = grid.length, n = grid[0].length, flat = grid.join(""), dist = new Array(m * n).fill(-1), queue = [];
  for (let i = 0; i < flat.length; i++) if (flat[i] === "P") { dist[i] = 0; queue.push(i); }
  for (let head = 0; head < queue.length; head++) {
    const i = queue[head], r = Math.floor(i / n), c = i - r * n;
    const visit = (j) => { if (dist[j] < 0 && flat[j] !== "X") { dist[j] = dist[i] + 1; queue.push(j); } };
    if (r > 0) visit(i - n);
    if (r < m - 1) visit(i + n);
    if (c > 0) visit(i - 1);
    if (c < n - 1) visit(i + 1);
  }
  let best = 0;
  for (let i = 0; i < flat.length; i++) {
    if (flat[i] === "-") { if (dist[i] < 0) return -1; if (dist[i] > best) best = dist[i]; }
  }
  return best;
}

function maxBuildingHeight(grid) { return solve(grid); }

module.exports = solve;
module.exports.maxBuildingHeight = maxBuildingHeight;
