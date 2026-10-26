'use strict';

// 1765. Map of Highest Peak: assign every cell its shortest distance to any water cell.
// O(rows * columns) time and O(rows * columns) space; inputs are read-only.
function solve(isWater) {
  const rows = isWater.length;
  const columns = isWater[0].length;
  const height = Array.from({ length: rows }, () => new Array(columns).fill(-1));
  const queue = new Int32Array(rows * columns);
  let head = 0;
  let tail = 0;
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      if (isWater[row][column] === 1) {
        height[row][column] = 0;
        queue[tail] = row * columns + column;
        tail += 1;
      }
    }
  }
  const directions = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  while (head < tail) {
    const cell = queue[head];
    head += 1;
    const row = Math.floor(cell / columns);
    const column = cell % columns;
    for (const [dr, dc] of directions) {
      const nr = row + dr;
      const nc = column + dc;
      if (nr >= 0 && nr < rows && nc >= 0 && nc < columns && height[nr][nc] === -1) {
        height[nr][nc] = height[row][column] + 1;
        queue[tail] = nr * columns + nc;
        tail += 1;
      }
    }
  }
  return height;
}

const highestPeak = solve;
class Solution {
  highestPeak(isWater) { return solve(isWater); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, highestPeak };
