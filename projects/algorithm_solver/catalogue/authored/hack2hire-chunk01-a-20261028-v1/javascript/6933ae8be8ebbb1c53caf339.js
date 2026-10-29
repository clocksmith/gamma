"use strict";
// Hack2Hire 6933ae8be8ebbb1c53caf339 (Count Islands and Water Boundary) over an INFERRED spec; qualification unknown.
function solve(grid) {
  const rows = grid.length, cols = grid[0].length, seen = new Uint8Array(rows * cols), result = [];
  const queue = new Int32Array(rows * cols);
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      if (grid[r][c] !== "1" || seen[r * cols + c]) continue;
      seen[r * cols + c] = 1;
      let head = 0, tail = 0, area = 0, boundary = 0;
      queue[tail++] = r * cols + c;
      while (head < tail) {
        const cell = queue[head++], x = Math.floor(cell / cols), y = cell % cols;
        area++;
        for (const [nx, ny] of [[x - 1, y], [x + 1, y], [x, y - 1], [x, y + 1]]) {
          if (nx < 0 || nx >= rows || ny < 0 || ny >= cols) continue;
          if (grid[nx][ny] === "0") boundary++;
          else if (!seen[nx * cols + ny]) { seen[nx * cols + ny] = 1; queue[tail++] = nx * cols + ny; }
        }
      }
      result.push([area, boundary]);
    }
  }
  return result;
}
function islandStats(grid) { return solve(grid); }
module.exports = solve;
module.exports.islandStats = islandStats;
