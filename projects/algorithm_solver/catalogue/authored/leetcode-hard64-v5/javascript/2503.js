'use strict';

// 2503. Maximum Number of Points From Grid Queries. Process sorted query thresholds through a shared minimum-heap frontier; O(m*n log(m*n)+q log q) time and O(m*n+q) space. Inputs are preserved.

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

function solve(grid, queries) {
  const rows = grid.length;
  const columns = grid[0].length;
  const seen = Array.from({ length: rows }, () => Array(columns).fill(false));
  seen[0][0] = true;
  const heap = new MinHeap((a, b) => a[0] < b[0]);
  heap.push([grid[0][0], 0, 0]);
  const answer = Array(queries.length).fill(0);
  const ordered = queries.map((value, index) => [value, index]).sort((a, b) => a[0] - b[0]);
  const directions = [[-1, 0], [1, 0], [0, -1], [0, 1]];
  let count = 0;
  for (const [threshold, index] of ordered) {
    while (heap.size > 0 && heap.peek()[0] < threshold) {
      const [, row, column] = heap.pop();
      count += 1;
      for (const [dr, dc] of directions) {
        const nextRow = row + dr;
        const nextColumn = column + dc;
        if (nextRow < 0 || nextRow >= rows || nextColumn < 0 || nextColumn >= columns || seen[nextRow][nextColumn]) continue;
        seen[nextRow][nextColumn] = true;
        heap.push([grid[nextRow][nextColumn], nextRow, nextColumn]);
      }
    }
    answer[index] = count;
  }
  return answer;
}

const maxPoints = solve;
class Solution {
  maxPoints(grid, queries) { return solve(grid, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxPoints };
