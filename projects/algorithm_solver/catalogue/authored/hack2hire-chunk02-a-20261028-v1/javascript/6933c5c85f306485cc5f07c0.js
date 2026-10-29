"use strict";
// Hack2Hire 6933c5c85f306485cc5f07c0 (Maximum Island Perimeter); INFERRED spec; qualification unknown.
const DR = [-1, 1, 0, 0], DC = [0, 0, -1, 1];
function solve(grid) {
  const rows = grid.length, cols = grid[0].length, seen = new Uint8Array(rows * cols);
  const land = (r, c) => r >= 0 && r < rows && c >= 0 && c < cols && grid[r][c] === '1';
  let best = 0;
  for (let r0 = 0; r0 < rows; r0++) for (let c0 = 0; c0 < cols; c0++) {
    if (grid[r0][c0] !== '1' || seen[r0 * cols + c0]) continue;
    seen[r0 * cols + c0] = 1;
    const stack = [r0 * cols + c0];
    let perimeter = 0;
    while (stack.length) {
      const cell = stack.pop(), r = Math.floor(cell / cols), c = cell % cols;
      for (let d = 0; d < 4; d++) {
        const nr = r + DR[d], nc = c + DC[d];
        if (!land(nr, nc)) perimeter++;
        else if (!seen[nr * cols + nc]) { seen[nr * cols + nc] = 1; stack.push(nr * cols + nc); }
      }
    }
    if (perimeter > best) best = perimeter;
  }
  return best;
}
function maxIslandPerimeter(grid) { return solve(grid); }
module.exports = solve;
module.exports.maxIslandPerimeter = maxIslandPerimeter;
