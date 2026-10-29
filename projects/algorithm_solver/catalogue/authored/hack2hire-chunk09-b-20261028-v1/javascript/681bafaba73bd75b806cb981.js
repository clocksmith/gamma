"use strict";
// Hack2Hire 681bafaba73bd75b806cb981 (Count Objects in Pin) over an INFERRED spec; qualification unknown.

function solve(grid, objectIds) {
  const rows = grid.length, cols = grid[0].length, size = rows * cols;
  const isSameObject = (r1, c1, r2, c2) => grid[r1][c1] === '*' && grid[r2][c2] === '*' && objectIds[r1][c1] === objectIds[r2][c2];
  const seen = new Uint8Array(size), queue = new Int32Array(size);
  let objects = 0;
  for (let start = 0; start < size; start++) {
    const r0 = (start / cols) | 0, c0 = start - r0 * cols;
    if (seen[start] || grid[r0][c0] !== '*') continue;
    objects++;
    seen[start] = 1;
    let head = 0, tail = 0;
    queue[tail++] = start;
    while (head < tail) {
      const cell = queue[head++], r = (cell / cols) | 0, c = cell - r * cols;
      if (r > 0 && !seen[cell - cols] && isSameObject(r, c, r - 1, c)) { seen[cell - cols] = 1; queue[tail++] = cell - cols; }
      if (r + 1 < rows && !seen[cell + cols] && isSameObject(r, c, r + 1, c)) { seen[cell + cols] = 1; queue[tail++] = cell + cols; }
      if (c > 0 && !seen[cell - 1] && isSameObject(r, c, r, c - 1)) { seen[cell - 1] = 1; queue[tail++] = cell - 1; }
      if (c + 1 < cols && !seen[cell + 1] && isSameObject(r, c, r, c + 1)) { seen[cell + 1] = 1; queue[tail++] = cell + 1; }
    }
  }
  return objects;
}

function countObjects(grid, objectIds) { return solve(grid, objectIds); }

module.exports = solve;
module.exports.countObjects = countObjects;
