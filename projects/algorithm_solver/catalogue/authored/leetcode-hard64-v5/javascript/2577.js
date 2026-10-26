'use strict';

// 2577. Minimum Time to Visit a Cell In a Grid. Dijkstra with two-step waiting parity after a legal first move; O(m*n log(m*n)) time and O(m*n) space. Inputs are preserved.

class MinHeap {
  constructor(less) {
    this.items = [];
    this.less = less;
  }

  get size() { return this.items.length; }
  peek() { return this.items[0]; }

  push(value) {
    const items = this.items;
    let index = items.length;
    items.push(value);
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (!this.less(value, items[parent])) break;
      items[index] = items[parent];
      index = parent;
    }
    items[index] = value;
  }

  pop() {
    const items = this.items;
    const result = items[0];
    const value = items.pop();
    if (items.length === 0) return result;
    let index = 0;
    while (2 * index + 1 < items.length) {
      let child = 2 * index + 1;
      if (child + 1 < items.length && this.less(items[child + 1], items[child])) child += 1;
      if (!this.less(items[child], value)) break;
      items[index] = items[child];
      index = child;
    }
    items[index] = value;
    return result;
  }
}

function solve(grid) {
  const rows = grid.length;
  const columns = grid[0].length;
  if (rows === 1 && columns === 1) return 0;
  if (!((rows > 1 && grid[1][0] <= 1) || (columns > 1 && grid[0][1] <= 1))) return -1;
  const distance = Array.from({ length: rows }, () => Array(columns).fill(Infinity));
  distance[0][0] = 0;
  const heap = new MinHeap((a, b) => a[0] < b[0]);
  heap.push([0, 0, 0]);
  const directions = [[-1, 0], [1, 0], [0, -1], [0, 1]];
  while (heap.size > 0) {
    const [elapsed, row, column] = heap.pop();
    if (elapsed !== distance[row][column]) continue;
    if (row === rows - 1 && column === columns - 1) return elapsed;
    for (const [dr, dc] of directions) {
      const nextRow = row + dr;
      const nextColumn = column + dc;
      if (nextRow < 0 || nextRow >= rows || nextColumn < 0 || nextColumn >= columns) continue;
      let arrival = elapsed + 1;
      const gate = grid[nextRow][nextColumn];
      if (arrival < gate) arrival = gate + (gate - arrival) % 2;
      if (arrival < distance[nextRow][nextColumn]) {
        distance[nextRow][nextColumn] = arrival;
        heap.push([arrival, nextRow, nextColumn]);
      }
    }
  }
  return -1;
}

const minimumTime = solve;
class Solution {
  minimumTime(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumTime };
