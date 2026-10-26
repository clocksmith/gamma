'use strict';

// 2258. Escape the Spreading Fire. Fire-arrival BFS and binary search on the initial wait; O(R*C*log(10^9)) time, O(R*C) space. Inputs are preserved.

function solve(grid) {
  const rows = grid.length;
  const columns = grid[0].length;
  const count = rows * columns;
  const fire = Array(count).fill(Infinity);
  const queue = [];
  const directions = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      if (grid[row][column] === 1) {
        const cell = row * columns + column;
        fire[cell] = 0;
        queue.push(cell);
      }
    }
  }
  for (let head = 0; head < queue.length; head += 1) {
    const cell = queue[head];
    const row = Math.floor(cell / columns);
    const column = cell % columns;
    for (const [dr, dc] of directions) {
      const nr = row + dr;
      const nc = column + dc;
      if (nr < 0 || nr >= rows || nc < 0 || nc >= columns || grid[nr][nc] === 2) continue;
      const target = nr * columns + nc;
      if (fire[target] === Infinity) {
        fire[target] = fire[cell] + 1;
        queue.push(target);
      }
    }
  }
  function feasible(wait) {
    if (wait >= fire[0]) return false;
    const arrival = new Float64Array(count).fill(-1);
    arrival[0] = wait;
    const pending = [0];
    for (let head = 0; head < pending.length; head += 1) {
      const cell = pending[head];
      if (cell === count - 1) return true;
      const row = Math.floor(cell / columns);
      const column = cell % columns;
      const following = arrival[cell] + 1;
      for (const [dr, dc] of directions) {
        const nr = row + dr;
        const nc = column + dc;
        if (nr < 0 || nr >= rows || nc < 0 || nc >= columns || grid[nr][nc] === 2) continue;
        const target = nr * columns + nc;
        if (arrival[target] >= 0) continue;
        if (target === count - 1 ? following > fire[target] : following >= fire[target]) continue;
        arrival[target] = following;
        pending.push(target);
      }
    }
    return false;
  }
  if (!feasible(0)) return -1;
  let left = 0;
  let right = 1000000000;
  while (left < right) {
    const middle = Math.floor((left + right + 1) / 2);
    if (feasible(middle)) left = middle;
    else right = middle - 1;
  }
  return left;
}

const maximumMinutes = solve;
class Solution {
  maximumMinutes(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumMinutes };
