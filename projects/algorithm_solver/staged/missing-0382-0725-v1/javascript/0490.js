'use strict';

// 490. The Maze.

function solve(maze, start, destination) {
  const rows = maze.length, cols = maze[0].length;
  const queue = [start.slice()], seen = new Set([start[0] * cols + start[1]]);
  for (let head = 0; head < queue.length; head += 1) {
    const [row, col] = queue[head];
    if (row === destination[0] && col === destination[1]) return true;
    for (const [dr, dc] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      let nr = row, nc = col;
      while (nr + dr >= 0 && nr + dr < rows && nc + dc >= 0 && nc + dc < cols && maze[nr + dr][nc + dc] === 0) { nr += dr; nc += dc; }
      const key = nr * cols + nc;
      if (!seen.has(key)) { seen.add(key); queue.push([nr, nc]); }
    }
  }
  return false;
}

const hasPath = solve;
class Solution {
  hasPath(maze, start, destination) { return solve(maze, start, destination); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, hasPath };
