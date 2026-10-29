"use strict";
// Hack2Hire 68edba975abdefad4f6693e3 (Grid Coloring with Boundaries) over an INFERRED spec; qualification unknown.

function solve(grid) {
  const m = grid.length, n = grid[0].length;
  const out = grid.map((row) => row.slice());
  const seen = new Uint8Array(m * n), region = new Int32Array(m * n);
  for (let first = 0; first < m * n; first++) {
    const r0 = Math.floor(first / n), c0 = first - r0 * n;
    if (seen[first] || grid[r0][c0] === -1) continue;
    seen[first] = 1;
    let size = 0, head = 0;
    region[size++] = first;
    while (head < size) {
      const cell = region[head++], r = Math.floor(cell / n), c = cell - r * n;
      if (r > 0 && grid[r - 1][c] !== -1 && !seen[cell - n]) { seen[cell - n] = 1; region[size++] = cell - n; }
      if (r + 1 < m && grid[r + 1][c] !== -1 && !seen[cell + n]) { seen[cell + n] = 1; region[size++] = cell + n; }
      if (c > 0 && grid[r][c - 1] !== -1 && !seen[cell - 1]) { seen[cell - 1] = 1; region[size++] = cell - 1; }
      if (c + 1 < n && grid[r][c + 1] !== -1 && !seen[cell + 1]) { seen[cell + 1] = 1; region[size++] = cell + 1; }
    }
    let base = -1;
    for (let i = 0; i < size; i++) {
      const cell = region[i], r = Math.floor(cell / n), c = cell - r * n;
      if (grid[r][c] !== 9) {
        const want = grid[r][c] ^ ((r + c) & 1);
        if (base === -1) base = want; else if (base !== want) return [];
      }
    }
    if (base === -1) base = 1 ^ ((r0 + c0) & 1);
    for (let i = 0; i < size; i++) {
      const cell = region[i], r = Math.floor(cell / n), c = cell - r * n;
      out[r][c] = base ^ ((r + c) & 1);
    }
  }
  return out;
}

function colorGrid(grid) { return solve(grid); }

module.exports = solve;
module.exports.colorGrid = colorGrid;
