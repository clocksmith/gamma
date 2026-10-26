'use strict';

// 1878. Get Biggest Three Rhombus Sums in a Grid: sum four diagonal borders and remove their double-counted corners.
// O(rows * columns * min(rows, columns)) time and O(rows * columns) auxiliary space; inputs are read-only.
function solve(grid) {
  const rows = grid.length;
  const columns = grid[0].length;
  const downRight = Array.from({ length: rows + 1 }, () => new Array(columns + 1).fill(0));
  const downLeft = Array.from({ length: rows + 1 }, () => new Array(columns + 1).fill(0));
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      downRight[row + 1][column + 1] = grid[row][column] + downRight[row][column];
      downLeft[row + 1][column] = grid[row][column] + downLeft[row][column + 1];
    }
  }
  const largest = new Set();
  function retain(value) {
    largest.add(value);
    if (largest.size > 3) {
      let smallest = Infinity;
      for (const item of largest) smallest = Math.min(smallest, item);
      largest.delete(smallest);
    }
  }
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      retain(grid[row][column]);
      const limit = Math.min(row, column, rows - 1 - row, columns - 1 - column);
      for (let radius = 1; radius <= limit; radius += 1) {
        let total = downRight[row + 1][column + radius + 1] - downRight[row - radius][column];
        total += downLeft[row + radius + 1][column] - downLeft[row][column + radius + 1];
        total += downRight[row + radius + 1][column + 1] - downRight[row][column - radius];
        total += downLeft[row + 1][column - radius] - downLeft[row - radius][column + 1];
        total -= grid[row - radius][column] + grid[row][column + radius] +
                 grid[row + radius][column] + grid[row][column - radius];
        retain(total);
      }
    }
  }
  return Array.from(largest).sort((a, b) => b - a);
}

const getBiggestThree = solve;
class Solution {
  getBiggestThree(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getBiggestThree };
