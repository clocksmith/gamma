'use strict';

// 2290. Minimum Obstacle Removal to Reach Corner.
// 0-1 BFS: O(rows*cols) expected time and space. Map-backed deque avoids Array.shift().
function solve(grid) {
  const rows = grid.length;
  const cols = grid[0].length;
  const size = rows * cols;
  const distance = new Int32Array(size).fill(size + 1);
  distance[0] = 0;
  const queue = new Map([[0, [0, 0]]]);
  let head = 0;
  let tail = 1;
  const directions = [[-1, 0], [1, 0], [0, -1], [0, 1]];
  while (head < tail) {
    const [node, cost] = queue.get(head);
    queue.delete(head);
    head += 1;
    if (cost !== distance[node]) continue;
    if (node === size - 1) return cost;
    const row = Math.floor(node / cols);
    const col = node % cols;
    for (const [dr, dc] of directions) {
      const nextRow = row + dr;
      const nextCol = col + dc;
      if (nextRow < 0 || nextRow >= rows || nextCol < 0 || nextCol >= cols) continue;
      const following = nextRow * cols + nextCol;
      const weight = grid[nextRow][nextCol];
      const candidate = cost + weight;
      if (candidate >= distance[following]) continue;
      distance[following] = candidate;
      if (weight === 0) {
        head -= 1;
        queue.set(head, [following, candidate]);
      } else {
        queue.set(tail, [following, candidate]);
        tail += 1;
      }
    }
  }
  return distance[size - 1];
}

const minimumObstacles = solve;
class Solution {
  minimumObstacles(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumObstacles };
