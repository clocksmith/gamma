"use strict";
// Hack2Hire 68f9a7290fa32e4d82f4fb89 (Find Nearest Exit in Maze, variant 2 of 2) over an INFERRED spec; qualification unknown.

function solve(matrix, entrance) {
  const m = matrix.length, n = matrix[0].length, start = entrance[0] * n + entrance[1];
  const seen = new Uint8Array(m * n);
  seen[start] = 1;
  let level = [start], distance = 0;
  while (level.length) {
    let best = -1;
    for (const v of level) {
      const c = v % n;
      if (v !== start && (v < n || v >= (m - 1) * n || c === 0 || c === n - 1) && (best < 0 || v < best)) best = v;
    }
    if (best >= 0) return [(best - best % n) / n, best % n];
    const following = [];
    for (const v of level) {
      const r = (v - v % n) / n, c = v % n;
      if (r > 0 && matrix[r - 1][c] === 1 && !seen[v - n]) { seen[v - n] = 1; following.push(v - n); }
      if (r < m - 1 && matrix[r + 1][c] === 1 && !seen[v + n]) { seen[v + n] = 1; following.push(v + n); }
      if (c > 0 && matrix[r][c - 1] === 1 && !seen[v - 1]) { seen[v - 1] = 1; following.push(v - 1); }
      if (c < n - 1 && matrix[r][c + 1] === 1 && !seen[v + 1]) { seen[v + 1] = 1; following.push(v + 1); }
    }
    level = following; distance++;
  }
  return [-1, -1];
}

function nearestExitCell(matrix, entrance) { return solve(matrix, entrance); }

module.exports = solve;
module.exports.nearestExitCell = nearestExitCell;
