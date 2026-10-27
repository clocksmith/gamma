'use strict';

// 499. The Maze III. Dijkstra orders by traveled distance and then direction string; stop rolling at the hole.

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

function solve(maze, ball, hole) {
  const rows = maze.length, cols = maze[0].length;
  const heap = new _Heap((a, b) => a[0] < b[0] || (a[0] === b[0] && a[1] < b[1]));
  const best = new Map([[ball[0] * cols + ball[1], [0, '']]]);
  heap.push([0, '', ball[0], ball[1]]);
  while (heap.size > 0) {
    const [distance, path, row, col] = heap.pop(), current = best.get(row * cols + col);
    if (current[0] !== distance || current[1] !== path) continue;
    if (row === hole[0] && col === hole[1]) return path;
    for (const [dr, dc, letter] of [[1, 0, 'd'], [0, -1, 'l'], [0, 1, 'r'], [-1, 0, 'u']]) {
      let nr = row, nc = col, steps = 0;
      while (nr + dr >= 0 && nr + dr < rows && nc + dc >= 0 && nc + dc < cols && maze[nr + dr][nc + dc] === 0) {
        nr += dr; nc += dc; steps += 1;
        if (nr === hole[0] && nc === hole[1]) break;
      }
      const key = nr * cols + nc, nextDistance = distance + steps, nextPath = path + letter, old = best.get(key);
      if (steps > 0 && (!old || nextDistance < old[0] || (nextDistance === old[0] && nextPath < old[1]))) {
        best.set(key, [nextDistance, nextPath]); heap.push([nextDistance, nextPath, nr, nc]);
      }
    }
  }
  return 'impossible';
}

const findShortestWay = solve;
class Solution {
  findShortestWay(maze, ball, hole) { return solve(maze, ball, hole); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findShortestWay };
