'use strict';

// 1706. Where Will the Ball Fall: follow each ball through adjacent boards of matching slope.
// O(rows * columns) time and O(columns) output space; inputs are read-only.
function solve(grid) {
  const columns = grid[0].length;
  const result = [];
  for (let start = 0; start < columns; start += 1) {
    let column = start;
    for (const row of grid) {
      const neighbor = column + row[column];
      if (neighbor < 0 || neighbor >= columns || row[neighbor] !== row[column]) {
        column = -1;
        break;
      }
      column = neighbor;
    }
    result.push(column);
  }
  return result;
}

const findBall = solve;
class Solution {
  findBall(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findBall };
