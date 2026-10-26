'use strict';

// 2617. Minimum Number of Visited Cells in a Grid. Row-major DP with expiring reachable-cell heaps per row and column; O(m*n log(m+n)) time and O(m*n) space. Inputs are preserved.

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
  const less = (a, b) => a[0] < b[0] || (a[0] === b[0] && a[1] < b[1]);
  const columnHeaps = Array.from({ length: columns }, () => new MinHeap(less));
  let distance = Infinity;
  for (let row = 0; row < rows; row += 1) {
    const rowHeap = new MinHeap(less);
    for (let column = 0; column < columns; column += 1) {
      const columnHeap = columnHeaps[column];
      while (rowHeap.size > 0 && rowHeap.peek()[1] < column) rowHeap.pop();
      while (columnHeap.size > 0 && columnHeap.peek()[1] < row) columnHeap.pop();
      distance = row === 0 && column === 0 ? 1 : Infinity;
      if (rowHeap.size > 0) distance = Math.min(distance, rowHeap.peek()[0] + 1);
      if (columnHeap.size > 0) distance = Math.min(distance, columnHeap.peek()[0] + 1);
      const reach = grid[row][column];
      if (distance !== Infinity && reach > 0) {
        rowHeap.push([distance, column + reach]);
        columnHeap.push([distance, row + reach]);
      }
    }
  }
  return distance === Infinity ? -1 : distance;
}

const minimumVisitedCells = solve;
class Solution {
  minimumVisitedCells(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumVisitedCells };
