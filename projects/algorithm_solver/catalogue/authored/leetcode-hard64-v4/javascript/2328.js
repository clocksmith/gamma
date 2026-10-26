'use strict';

// 2328. Number of Increasing Paths in a Grid. Value-ordered path DP with no recursive depth; O(R*C log(R*C)) time and O(R*C) space. Inputs are preserved.

function solve(grid) {
  const modulus = 1000000007;
  const rows = grid.length;
  const columns = grid[0].length;
  const order = Array.from({ length: rows * columns }, (_, cell) => cell);
  order.sort((a, b) => grid[Math.floor(a / columns)][a % columns] - grid[Math.floor(b / columns)][b % columns]);
  const ways = new Int32Array(rows * columns);
  const directions = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  let answer = 0;
  for (const cell of order) {
    const row = Math.floor(cell / columns);
    const column = cell % columns;
    let count = 1;
    for (const [dr, dc] of directions) {
      const nr = row + dr;
      const nc = column + dc;
      if (nr >= 0 && nr < rows && nc >= 0 && nc < columns && grid[nr][nc] < grid[row][column]) {
        count += ways[nr * columns + nc];
      }
    }
    ways[cell] = count % modulus;
    answer = (answer + ways[cell]) % modulus;
  }
  return answer;
}

const countPaths = solve;
class Solution {
  countPaths(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPaths };
