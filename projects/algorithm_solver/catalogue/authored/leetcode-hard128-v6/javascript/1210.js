'use strict';

// 1210. Minimum Moves to Reach Target with Rotations.
// Breadth-first search over tail position and orientation; O(n^2) time and space. Inputs are preserved.

function solve(grid) {
  const n = grid.length;
  const queue = [[0, 0, 0, 0]];
  const seen = new Set([0]);
  for (let head = 0; head < queue.length; head += 1) {
    const [row, column, vertical, distance] = queue[head];
    if (row === n - 1 && column === n - 2 && vertical === 0) return distance;
    const following = [];
    if (vertical === 0) {
      if (column + 2 < n && grid[row][column + 2] === 0) following.push([row, column + 1, 0]);
      if (row + 1 < n && grid[row + 1][column] === 0 && grid[row + 1][column + 1] === 0) {
        following.push([row + 1, column, 0], [row, column, 1]);
      }
    } else {
      if (row + 2 < n && grid[row + 2][column] === 0) following.push([row + 1, column, 1]);
      if (column + 1 < n && grid[row][column + 1] === 0 && grid[row + 1][column + 1] === 0) {
        following.push([row, column + 1, 1], [row, column, 0]);
      }
    }
    for (const state of following) {
      const key = (state[0] * n + state[1]) * 2 + state[2];
      if (!seen.has(key)) {
        seen.add(key);
        queue.push([...state, distance + 1]);
      }
    }
  }
  return -1;
}

const minimumMoves = solve;
class Solution {
  minimumMoves(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumMoves };
