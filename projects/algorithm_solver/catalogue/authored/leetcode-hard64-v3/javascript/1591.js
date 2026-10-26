'use strict';

// 1591. Strange Printer II: bounding-rectangle dependency graph; O(colors*rows*columns) time and O(colors^2) auxiliary space.

function solve(targetGrid) {
  const bounds = new Map();
  for (let row = 0; row < targetGrid.length; row += 1) {
    for (let column = 0; column < targetGrid[row].length; column += 1) {
      const color = targetGrid[row][column];
      if (!bounds.has(color)) bounds.set(color, [row, row, column, column]);
      const box = bounds.get(color);
      box[0] = Math.min(box[0], row);
      box[1] = Math.max(box[1], row);
      box[2] = Math.min(box[2], column);
      box[3] = Math.max(box[3], column);
    }
  }
  const following = new Map();
  const indegree = new Map();
  for (const color of bounds.keys()) {
    following.set(color, new Set());
    indegree.set(color, 0);
  }
  for (const [color, [top, bottom, left, right]] of bounds) {
    for (let row = top; row <= bottom; row += 1) {
      for (let column = left; column <= right; column += 1) {
        const other = targetGrid[row][column];
        if (other !== color && !following.get(color).has(other)) {
          following.get(color).add(other);
          indegree.set(other, indegree.get(other) + 1);
        }
      }
    }
  }
  const queue = [];
  for (const [color, degree] of indegree) if (degree === 0) queue.push(color);
  for (let head = 0; head < queue.length; head += 1) {
    for (const other of following.get(queue[head])) {
      indegree.set(other, indegree.get(other) - 1);
      if (indegree.get(other) === 0) queue.push(other);
    }
  }
  return queue.length === bounds.size;
}

const isPrintable = solve;
class Solution {
  isPrintable(targetGrid) { return solve(targetGrid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isPrintable };
