'use strict';

// 1914. Cyclically Rotating a Grid: rotate each clockwise boundary sequence by a counterclockwise offset into a fresh grid.
// O(rows * columns) time and output space, with O(rows + columns) auxiliary space; inputs are read-only.
function solve(grid, k) {
  const rows = grid.length;
  const columns = grid[0].length;
  const result = grid.map(row => row.slice());
  for (let layer = 0; layer < Math.floor(Math.min(rows, columns) / 2); layer += 1) {
    const top = layer;
    const left = layer;
    const bottom = rows - 1 - layer;
    const right = columns - 1 - layer;
    const boundary = [];
    for (let column = left; column <= right; column += 1) boundary.push([top, column]);
    for (let row = top + 1; row <= bottom; row += 1) boundary.push([row, right]);
    for (let column = right - 1; column >= left; column -= 1) boundary.push([bottom, column]);
    for (let row = bottom - 1; row > top; row -= 1) boundary.push([row, left]);
    const shift = k % boundary.length;
    for (let index = 0; index < boundary.length; index += 1) {
      const [row, column] = boundary[index];
      const [sourceRow, sourceColumn] = boundary[(index + shift) % boundary.length];
      result[row][column] = grid[sourceRow][sourceColumn];
    }
  }
  return result;
}

const rotateGrid = solve;
class Solution {
  rotateGrid(grid, k) { return solve(grid, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, rotateGrid };
