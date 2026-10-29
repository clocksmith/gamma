"use strict";
// Hack2Hire 6866f15ea2d59460201f2c7e (Matrix Escape) over an INFERRED spec; qualification unknown.

function solve(grid) {
  const m = grid.length, n = grid[0].length, flat = grid.join(""), size = m * n, inf = size + 1;
  const threat = new Array(size).fill(inf);
  let queue = [];
  for (let i = 0; i < size; i++) if (flat[i] === "P") { threat[i] = 0; queue.push(i); }
  const nbr = new Array(4);
  const neighbours = (i) => {
    const r = Math.floor(i / n), c = i - r * n;
    let k = 0;
    if (r > 0) nbr[k++] = i - n;
    if (r < m - 1) nbr[k++] = i + n;
    if (c > 0) nbr[k++] = i - 1;
    if (c < n - 1) nbr[k++] = i + 1;
    return k;
  };
  for (let head = 0; head < queue.length; head++) {
    const i = queue[head], k = neighbours(i);
    for (let t = 0; t < k; t++) { const j = nbr[t]; if (flat[j] !== "X" && threat[j] === inf) { threat[j] = threat[i] + 1; queue.push(j); } }
  }
  const start = flat.indexOf("U"), time = new Array(size).fill(-1);
  time[start] = 0;
  queue = [start];
  for (let head = 0; head < queue.length; head++) {
    const i = queue[head], r = Math.floor(i / n), c = i - r * n;
    if (r === 0 || c === 0 || r === m - 1 || c === n - 1) return time[i];
    const k = neighbours(i);
    for (let t = 0; t < k; t++) {
      const j = nbr[t];
      if (flat[j] !== "X" && time[j] < 0 && time[i] + 1 < threat[j]) { time[j] = time[i] + 1; queue.push(j); }
    }
  }
  return -1;
}

function escapeMatrix(grid) { return solve(grid); }

module.exports = solve;
module.exports.escapeMatrix = escapeMatrix;
