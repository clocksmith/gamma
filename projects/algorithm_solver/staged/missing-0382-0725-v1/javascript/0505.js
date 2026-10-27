'use strict';

// 505. The Maze II.

class _Heap {
  constructor(less = (a, b) => a < b) { this.data = []; this.less = less; }
  get size() { return this.data.length; }
  peek() { return this.data[0]; }
  push(value) {
    const a = this.data;
    let i = a.length;
    a.push(value);
    while (i > 0) {
      const parent = Math.floor((i - 1) / 2);
      if (!this.less(value, a[parent])) break;
      a[i] = a[parent];
      i = parent;
    }
    a[i] = value;
  }
  pop() {
    const a = this.data;
    if (a.length === 0) return undefined;
    const result = a[0];
    const last = a.pop();
    if (a.length > 0) {
      let i = 0;
      while (2 * i + 1 < a.length) {
        let child = 2 * i + 1;
        if (child + 1 < a.length && this.less(a[child + 1], a[child])) child += 1;
        if (!this.less(a[child], last)) break;
        a[i] = a[child];
        i = child;
      }
      a[i] = last;
    }
    return result;
  }
}

function solve(maze, start, destination) {
  const rows = maze.length, cols = maze[0].length;
  const distance = Array.from({length: rows}, () => Array(cols).fill(Infinity)), heap = new _Heap((a, b) => a[0] < b[0]);
  distance[start[0]][start[1]] = 0;
  heap.push([0, start[0], start[1]]);
  while (heap.size > 0) {
    const [cost, row, col] = heap.pop();
    if (cost !== distance[row][col]) continue;
    if (row === destination[0] && col === destination[1]) return cost;
    for (const [dr, dc] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      let nr = row, nc = col, steps = 0;
      while (nr + dr >= 0 && nr + dr < rows && nc + dc >= 0 && nc + dc < cols && maze[nr + dr][nc + dc] === 0) { nr += dr; nc += dc; steps += 1; }
      if (cost + steps < distance[nr][nc]) {
        distance[nr][nc] = cost + steps; heap.push([cost + steps, nr, nc]);
      }
    }
  }
  return -1;
}

const shortestDistance = solve;
class Solution {
  shortestDistance(maze, start, destination) { return solve(maze, start, destination); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, shortestDistance };
