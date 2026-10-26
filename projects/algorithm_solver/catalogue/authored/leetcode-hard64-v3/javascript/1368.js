'use strict';

// 1368. Minimum Cost to Make at Least One Valid Path in a Grid: 0-1 BFS, with zero cost for following an arrow; O(rows*columns) time and space.

function solve(grid) {
  const rows = grid.length;
  const columns = grid[0].length;
  const distance = Array.from({ length: rows }, () => Array(columns).fill(Infinity));
  distance[0][0] = 0;
  const queue = new Map([[0, [0, 0, 0]]]);
  let head = 0;
  let tail = 1;
  const directions = [[0, 1], [0, -1], [1, 0], [-1, 0]];
  while (head < tail) {
    const [row, column, cost] = queue.get(head);
    queue.delete(head);
    head += 1;
    if (cost !== distance[row][column]) continue;
    if (row === rows - 1 && column === columns - 1) return cost;
    for (let arrow = 0; arrow < directions.length; arrow += 1) {
      const nr = row + directions[arrow][0];
      const nc = column + directions[arrow][1];
      if (nr < 0 || nr >= rows || nc < 0 || nc >= columns) continue;
      const extra = grid[row][column] === arrow + 1 ? 0 : 1;
      const following = cost + extra;
      if (following < distance[nr][nc]) {
        distance[nr][nc] = following;
        if (extra === 0) {
          head -= 1;
          queue.set(head, [nr, nc, following]);
        } else {
          queue.set(tail, [nr, nc, following]);
          tail += 1;
        }
      }
    }
  }
  return -1;
}

const minCost = solve;
class Solution {
  minCost(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minCost };
